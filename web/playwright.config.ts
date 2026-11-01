import { defineConfig } from '@playwright/test';

// Runs against the production build (`bun run build` first), the same bundle Pages ships.
export default defineConfig({
  testDir: 'e2e',
  // Dates render through Intl; pin them so "31 Aug" reads the same on every machine.
  use: { baseURL: 'http://localhost:4173', locale: 'en-GB', timezoneId: 'UTC' },
  webServer: { command: 'bun run preview --port 4173 --strictPort', url: 'http://localhost:4173' },
});
