import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'path';
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
        port: 3021,
        host: true,
        open: true,
    },
    build: {
        outDir: 'dist',
        sourcemap: true,
    },
});
