import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
export default defineConfig({
  plugins:[react()],
  build:{outDir:'dist-observatory',copyPublicDir:false},
  server:{host:'127.0.0.1',port:5173,watch:{ignored:['**/deliverables/**','**/research/**','**/.build/**','**/.python-deps/**','**/data/raw/**','**/slides/**']}},
  preview:{host:'127.0.0.1',port:4173}
});
