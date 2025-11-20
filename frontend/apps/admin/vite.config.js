import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'path';
import { fileURLToPath } from 'url';
var __dirname = path.dirname(fileURLToPath(import.meta.url));
export default defineConfig({
    root: __dirname,
    plugins: [react()],
    resolve: {
        alias: {
            '@': path.resolve(__dirname, '../../'),
            '@/packages': path.resolve(__dirname, '../../packages'),
        },
    },
    server: {
        port: 3023,
        host: true,
    },
    build: {
        outDir: 'dist',
        sourcemap: true,
    },
});
