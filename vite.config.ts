import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import { resolve } from 'path';
import { copyFileSync, existsSync, mkdirSync } from 'fs';

// Plugin to copy overlay.html to dist root
const copyOverlayPlugin = () => ({
  name: 'copy-overlay',
  closeBundle() {
    const srcPath = resolve(__dirname, 'public/overlay.html');
    const distPath = resolve(__dirname, 'dist/overlay.html');
    if (existsSync(srcPath)) {
      copyFileSync(srcPath, distPath);
    }
  },
});

export default defineConfig({
  plugins: [react(), copyOverlayPlugin()],
  base: './',
  server: {
    port: 5173,
    strictPort: true,
  },
  build: {
    outDir: 'dist',
    emptyOutDir: true,
  },
});
