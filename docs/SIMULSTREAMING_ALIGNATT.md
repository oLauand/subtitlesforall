# SimulStreaming AlignAtt - Streaming Optimization for Real-Time Transcription

## Overview

SimulStreaming AlignAtt is an experimental streaming optimization for whisper.cpp based on the research paper ["Improving Streaming Whisper for Real-Time Speech Recognition"](https://arxiv.org/abs/2309.05096). This feature uses cross-attention weights to determine optimal decoding timing, reducing latency for real-time transcription applications.

## How It Works

Traditional Whisper streaming requires waiting for a fixed audio duration before transcribing, causing unnecessary latency. AlignAtt (Attention-based Alignment) analyzes the model's cross-attention patterns to determine exactly when the decoder's attention has reached the boundary of the available audio, allowing early stopping of token generation.

### Key Concept

During decoding, Whisper's cross-attention mechanism shows where in the audio the model is "looking" for each generated token. When the attention focus gets too close to the end of the currently available audio (within a configurable threshold), we stop decoding and return partial results. This prevents:

- Hallucinations at audio boundaries
- Unnecessary waiting for more audio
- Repetitive or stuck decoding loops

## API Reference

### Parameters

#### `whisper_alignatt_params`

```c
typedef struct whisper_alignatt_params {
    bool   enabled;              // Enable AlignAtt streaming policy
    int    frame_threshold;      // Frames from audio end before stopping (default: 25 = 250ms)
    int    min_tokens;           // Minimum tokens before AlignAtt check (default: 1)
    int    attention_layer;      // Which layer's cross-attention to use (-1 = last layer)
    int    attention_head;       // Which head to use (-1 = average all heads)
    bool   store_attention;      // Store cross-attention weights for analysis
} whisper_alignatt_params;
```

#### `whisper_streaming_params`

```c
typedef struct whisper_streaming_params {
    struct whisper_alignatt_params alignatt;  // AlignAtt policy parameters
    int    chunk_ms;                          // Audio chunk size in ms (default: 1000)
    int    context_tokens;                    // Context tokens to preserve (default: 224)
    float  vad_threshold;                     // VAD threshold (default: 0.5)
    bool   use_vad;                           // Enable VAD (default: false)
} whisper_streaming_params;
```

### Functions

#### Default Parameters

```c
struct whisper_alignatt_params whisper_alignatt_default_params(void);
struct whisper_streaming_params whisper_streaming_default_params(void);
```

#### Streaming Context

```c
// Initialize streaming context
struct whisper_streaming_context * whisper_streaming_init(
    struct whisper_context * ctx,
    struct whisper_streaming_params params);

// Insert audio samples into buffer
int whisper_streaming_insert_audio(
    struct whisper_streaming_context * sctx,
    const float * samples,
    int n_samples);

// Process buffered audio
int whisper_streaming_process(
    struct whisper_streaming_context * sctx,
    struct whisper_full_params params);

// Get finalized results
int whisper_streaming_n_segments(struct whisper_streaming_context * sctx);
const char * whisper_streaming_get_segment_text(struct whisper_streaming_context * sctx, int i);
int64_t whisper_streaming_get_segment_t0(struct whisper_streaming_context * sctx, int i);
int64_t whisper_streaming_get_segment_t1(struct whisper_streaming_context * sctx, int i);

// Get partial/in-progress text
const char * whisper_streaming_get_partial(struct whisper_streaming_context * sctx);

// Finalize stream (process remaining audio)
int whisper_streaming_finalize(struct whisper_streaming_context * sctx);

// Free resources
void whisper_streaming_free(struct whisper_streaming_context * sctx);
```

#### Direct AlignAtt Policy Functions

```c
// Check if decoding should stop based on attention position
bool whisper_alignatt_should_stop(
    struct whisper_state * state,
    struct whisper_alignatt_params params,
    int n_audio_frames);

// Get current attention focus frame position
int whisper_alignatt_get_attention_pos(
    struct whisper_state * state,
    struct whisper_alignatt_params params);
```

## Usage Example

### Basic Streaming Usage

```c
#include "whisper.h"

int main() {
    // Initialize Whisper context
    struct whisper_context_params cparams = whisper_context_default_params();
    cparams.store_cross_attention = true;  // Required for AlignAtt
    
    struct whisper_context * ctx = whisper_init_from_file_with_params(
        "ggml-base.en.bin", cparams);
    
    // Initialize streaming context
    struct whisper_streaming_params sparams = whisper_streaming_default_params();
    sparams.alignatt.enabled = true;
    sparams.alignatt.frame_threshold = 25;  // 250ms threshold
    sparams.chunk_ms = 1000;  // Process in 1-second chunks
    
    struct whisper_streaming_context * sctx = whisper_streaming_init(ctx, sparams);
    
    // Audio processing loop
    while (/* receiving audio */) {
        float * samples = /* get audio samples */;
        int n_samples = /* number of samples */;
        
        // Insert audio
        whisper_streaming_insert_audio(sctx, samples, n_samples);
        
        // Process
        struct whisper_full_params wparams = whisper_full_default_params(WHISPER_SAMPLING_GREEDY);
        wparams.single_segment = true;
        
        if (whisper_streaming_process(sctx, wparams) == 0) {
            // Get finalized segments
            int n = whisper_streaming_n_segments(sctx);
            for (int i = 0; i < n; i++) {
                printf("[%lld - %lld] %s\n",
                    whisper_streaming_get_segment_t0(sctx, i),
                    whisper_streaming_get_segment_t1(sctx, i),
                    whisper_streaming_get_segment_text(sctx, i));
            }
            
            // Get partial/in-progress text
            const char * partial = whisper_streaming_get_partial(sctx);
            if (partial && strlen(partial) > 0) {
                printf("(partial: %s)\n", partial);
            }
        }
    }
    
    // Finalize remaining audio
    whisper_streaming_finalize(sctx);
    
    // Cleanup
    whisper_streaming_free(sctx);
    whisper_free(ctx);
    
    return 0;
}
```

### Using AlignAtt with Standard API

You can also use AlignAtt with the standard `whisper_full()` API:

```c
struct whisper_full_params wparams = whisper_full_default_params(WHISPER_SAMPLING_GREEDY);

// Enable AlignAtt
wparams.alignatt.enabled = true;
wparams.alignatt.frame_threshold = 25;  // Stop 250ms before audio end

// Enable cross-attention storage in context
struct whisper_context_params cparams = whisper_context_default_params();
cparams.store_cross_attention = true;

// ... rest of standard usage
```

## Performance Tuning

### Frame Threshold

The `frame_threshold` parameter controls how early to stop decoding:

- **Lower values (10-15)**: More aggressive, lower latency, but may cut off words
- **Default (25)**: Balanced, 250ms buffer before audio end
- **Higher values (30-50)**: More conservative, higher latency, safer for complete words

### Recommendations

1. **Real-time transcription**: Use `frame_threshold = 20-25`
2. **Live captioning**: Use `frame_threshold = 25-30`
3. **Quality-focused**: Use `frame_threshold = 35-50`

## Limitations

1. **Flash Attention**: AlignAtt requires standard attention path. When `flash_attn = true`, cross-attention capture is not available in that path.

2. **Beam Search**: AlignAtt works with beam search but is most effective with greedy sampling.

3. **Memory**: Storing cross-attention weights requires additional memory proportional to `n_tokens × n_audio_ctx`.

4. **Experimental**: This feature is experimental and the API may change.

## Technical Details

### Cross-Attention Analysis

For each decoded token, we analyze the cross-attention pattern across all audio frames. The attention is averaged across all heads in the specified layer (default: last layer) to get a robust estimate of where the model is "looking".

The frame with maximum attention for the most recent token indicates the current focus point. When this position exceeds `n_audio_frames - frame_threshold`, we signal that decoding should stop.

### Frame to Time Conversion

- 1 frame = 10ms (WHISPER_HOP_LENGTH / WHISPER_SAMPLE_RATE = 160/16000)
- `frame_threshold = 25` means ~250ms from audio end
- Audio context typically covers 30 seconds (3000 frames)

## References

- Original Paper: [Improving Streaming Whisper for Real-Time Speech Recognition](https://arxiv.org/abs/2309.05096)
- Related: [SimulEval: Simultaneous Machine Translation Evaluation](https://github.com/facebookresearch/SimulEval)
