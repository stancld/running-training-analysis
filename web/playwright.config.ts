import { defineConfig } from '@playwright/test';

// Runs against the production build (`bun run build` first), the same bundle Pages ships.
export default defineConfig({
  testDir: 'e2e',
  // Dates render through Intl; pin them so "31 Aug" reads the same on every machine. A zone
  // behind UTC catches dates that slip to the previous day.
  use: { baseURL: 'http://localhost:4173', locale: 'en-GB', timezoneId: 'America/New_York' },
  webServer: { command: 'bun run preview --port 4173 --strictPort', url: 'http://localhost:4173' },
});
