import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  assetsInclude: ['**/*.glb', '**/*.gltf'],
  server: {
    host: true,
    port: 3000,
    strictPort: false,
  },
  build: {
    outDir: 'dist',
    target: 'esnext',
  },
});
