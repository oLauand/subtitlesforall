// SimulStreaming AlignAtt Example
// This example demonstrates real-time streaming transcription with AlignAtt policy
//
// Build:
//   cmake --build build --target stream-alignatt
//
// Run:
//   ./build/bin/stream-alignatt -m models/ggml-base.en.bin

#include "whisper.h"
#include "common-sdl.h"
#include "common.h"

#include <cstdio>
#include <cstring>
#include <string>
#include <thread>
#include <vector>
#include <atomic>

struct stream_alignatt_params {
    int32_t n_threads  = std::min(4, (int32_t) std::thread::hardware_concurrency());
    int32_t step_ms    = 1000;  // Audio step size in ms
    int32_t length_ms  = 3000;  // Audio length to process in ms
    int32_t keep_ms    = 200;   // Audio to keep from previous step
    int32_t capture_id = -1;
    int32_t frame_threshold = 25;  // AlignAtt frame threshold (250ms default)

    bool use_vad      = false;
    bool translate    = false;
    bool print_energy = false;
    bool no_timestamps = false;

    std::string language  = "en";
    std::string model     = "models/ggml-base.en.bin";
};

void usage(const char * prog) {
    fprintf(stderr, "\n");
    fprintf(stderr, "usage: %s [options]\n", prog);
    fprintf(stderr, "\n");
    fprintf(stderr, "options:\n");
    fprintf(stderr, "  -h,        --help              show this help message\n");
    fprintf(stderr, "  -t N,      --threads N         number of threads (default: %d)\n", 4);
    fprintf(stderr, "  --step N                       audio step size in ms (default: 1000)\n");
    fprintf(stderr, "  --length N                     audio length in ms (default: 3000)\n");
    fprintf(stderr, "  --keep N                       audio to keep from previous step in ms (default: 200)\n");
    fprintf(stderr, "  -c ID,     --capture ID        capture device ID (default: -1)\n");
    fprintf(stderr, "  --alignatt-threshold N         AlignAtt frame threshold (default: 25 = 250ms)\n");
    fprintf(stderr, "  --vad                          enable VAD\n");
    fprintf(stderr, "  -tr,       --translate         translate to English\n");
    fprintf(stderr, "  -l LANG,   --language LANG     language (default: en)\n");
    fprintf(stderr, "  -m FILE,   --model FILE        model path (default: models/ggml-base.en.bin)\n");
    fprintf(stderr, "  --print-energy                 print audio energy\n");
    fprintf(stderr, "  -nt,       --no-timestamps     disable timestamps\n");
    fprintf(stderr, "\n");
}

bool parse_args(int argc, char ** argv, stream_alignatt_params & params) {
    for (int i = 1; i < argc; i++) {
        std::string arg = argv[i];

        if (arg == "-h" || arg == "--help") {
            usage(argv[0]);
            return false;
        }
        else if (arg == "-t" || arg == "--threads") {
            params.n_threads = std::stoi(argv[++i]);
        }
        else if (arg == "--step") {
            params.step_ms = std::stoi(argv[++i]);
        }
        else if (arg == "--length") {
            params.length_ms = std::stoi(argv[++i]);
        }
        else if (arg == "--keep") {
            params.keep_ms = std::stoi(argv[++i]);
        }
        else if (arg == "-c" || arg == "--capture") {
            params.capture_id = std::stoi(argv[++i]);
        }
        else if (arg == "--alignatt-threshold") {
            params.frame_threshold = std::stoi(argv[++i]);
        }
        else if (arg == "--vad") {
            params.use_vad = true;
        }
        else if (arg == "-tr" || arg == "--translate") {
            params.translate = true;
        }
        else if (arg == "-l" || arg == "--language") {
            params.language = argv[++i];
        }
        else if (arg == "-m" || arg == "--model") {
            params.model = argv[++i];
        }
        else if (arg == "--print-energy") {
            params.print_energy = true;
        }
        else if (arg == "-nt" || arg == "--no-timestamps") {
            params.no_timestamps = true;
        }
        else {
            fprintf(stderr, "error: unknown argument: %s\n", arg.c_str());
            usage(argv[0]);
            return false;
        }
    }

    return true;
}

int main(int argc, char ** argv) {
    stream_alignatt_params params;

    if (!parse_args(argc, argv, params)) {
        return 1;
    }

    // Initialize audio capture
    audio_async audio(params.length_ms);
    if (!audio.init(params.capture_id, WHISPER_SAMPLE_RATE)) {
        fprintf(stderr, "%s: audio.init() failed!\n", __func__);
        return 1;
    }

    audio.resume();

    // Initialize whisper context with cross-attention storage enabled
    struct whisper_context_params cparams = whisper_context_default_params();
    cparams.store_cross_attention = true;  // Required for AlignAtt

    struct whisper_context * ctx = whisper_init_from_file_with_params(params.model.c_str(), cparams);
    if (ctx == nullptr) {
        fprintf(stderr, "%s: failed to load model '%s'\n", __func__, params.model.c_str());
        return 1;
    }

    // Initialize streaming context with AlignAtt
    struct whisper_streaming_params sparams = whisper_streaming_default_params();
    sparams.alignatt.enabled = true;
    sparams.alignatt.frame_threshold = params.frame_threshold;
    sparams.chunk_ms = params.step_ms;
    sparams.use_vad = params.use_vad;

    struct whisper_streaming_context * sctx = whisper_streaming_init(ctx, sparams);
    if (sctx == nullptr) {
        fprintf(stderr, "%s: failed to initialize streaming context\n", __func__);
        whisper_free(ctx);
        return 1;
    }

    printf("[SimulStreaming AlignAtt Example]\n");
    printf("  Model:              %s\n", params.model.c_str());
    printf("  AlignAtt threshold: %d frames (%d ms)\n", params.frame_threshold, params.frame_threshold * 10);
    printf("  Step size:          %d ms\n", params.step_ms);
    printf("  Language:           %s\n", params.language.c_str());
    printf("\nStart speaking...\n\n");

    std::vector<float> pcmf32_cur;
    std::vector<float> pcmf32_old;

    bool is_running = true;
    std::atomic<bool> should_stop{false};

    // Main loop
    while (is_running) {
        // Get audio from capture device
        audio.get(params.step_ms, pcmf32_cur);

        if (pcmf32_cur.empty()) {
            std::this_thread::sleep_for(std::chrono::milliseconds(10));
            continue;
        }

        // Combine with kept audio from previous step
        std::vector<float> pcmf32;
        pcmf32.reserve(pcmf32_old.size() + pcmf32_cur.size());
        pcmf32.insert(pcmf32.end(), pcmf32_old.begin(), pcmf32_old.end());
        pcmf32.insert(pcmf32.end(), pcmf32_cur.begin(), pcmf32_cur.end());

        // Keep some audio for next step
        const int n_keep = (params.keep_ms * WHISPER_SAMPLE_RATE) / 1000;
        if ((int)pcmf32.size() > n_keep) {
            pcmf32_old.assign(pcmf32.end() - n_keep, pcmf32.end());
        } else {
            pcmf32_old = pcmf32;
        }

        // Insert audio into streaming context
        whisper_streaming_insert_audio(sctx, pcmf32.data(), pcmf32.size());

        // Configure processing parameters
        struct whisper_full_params wparams = whisper_full_default_params(WHISPER_SAMPLING_GREEDY);
        wparams.n_threads        = params.n_threads;
        wparams.language         = params.language.c_str();
        wparams.translate        = params.translate;
        wparams.single_segment   = true;
        wparams.no_timestamps    = params.no_timestamps;
        wparams.print_special    = false;
        wparams.print_progress   = false;
        wparams.print_realtime   = false;
        wparams.print_timestamps = !params.no_timestamps;

        // Process with AlignAtt
        int ret = whisper_streaming_process(sctx, wparams);
        if (ret != 0) {
            fprintf(stderr, "whisper_streaming_process() failed: %d\n", ret);
            continue;
        }

        // Print finalized segments
        int n_segments = whisper_streaming_n_segments(sctx);
        for (int i = 0; i < n_segments; i++) {
            const char * text = whisper_streaming_get_segment_text(sctx, i);
            int64_t t0 = whisper_streaming_get_segment_t0(sctx, i);
            int64_t t1 = whisper_streaming_get_segment_t1(sctx, i);

            if (!params.no_timestamps) {
                printf("[%02d:%02d.%03d - %02d:%02d.%03d] ",
                    (int)(t0 / 6000), (int)((t0 % 6000) / 100), (int)(t0 % 100) * 10,
                    (int)(t1 / 6000), (int)((t1 % 6000) / 100), (int)(t1 % 100) * 10);
            }
            printf("%s\n", text);
            fflush(stdout);
        }

        // Print partial text (work in progress)
        const char * partial = whisper_streaming_get_partial(sctx);
        if (partial && strlen(partial) > 0) {
            printf("\033[90m(partial: %s)\033[0m\r", partial);
            fflush(stdout);
        }

        // Check for keyboard input to quit
        // (simplified - in real app would use proper input handling)
    }

    // Finalize streaming
    whisper_streaming_finalize(sctx);

    // Print any remaining segments
    int n_final = whisper_streaming_n_segments(sctx);
    for (int i = 0; i < n_final; i++) {
        printf("[FINAL] %s\n", whisper_streaming_get_segment_text(sctx, i));
    }

    // Cleanup
    whisper_streaming_free(sctx);
    whisper_free(ctx);

    return 0;
}
