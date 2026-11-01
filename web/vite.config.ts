import react from '@vitejs/plugin-react';
import { defineConfig } from 'vite';

export default defineConfig({
  plugins: [react()],
  // Relative asset URLs: Pages serves the site under /running-training-analysis/.
  base: './',
  // The orb portal proxies the dev server under its own hostname.
  server: { allowedHosts: true },
});
