import { expect, test, type Page } from '@playwright/test';

/* CI builds the page from scripts/synthetic_cache.sh: a race week (31 Aug – 6 Sep 2026,
   240 min RACE_Run), a ride-only week and a 105 km week flagged R2 and R6. Nothing here
   depends on today's date, which moves the current week and the countdown. */

async function open(page: Page) {
  const errors: string[] = [];
  page.on('pageerror', e => errors.push(e.message));
  page.on('console', m => m.type() === 'error' && errors.push(m.text()));
  // Google Fonts is the only external request; keep CI off the network.
  await page.route(/fonts\.(googleapis|gstatic)\.com/, r => r.fulfill({ contentType: 'text/css', body: '' }));
  await page.goto('/');
  await expect(page.locator('meta[name="robots"]')).toHaveAttribute('content', 'noindex, nofollow');
  return errors;
}

const noOverflow = async (page: Page) =>
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= document.documentElement.clientWidth)).toBe(
    true,
  );

test('laptop: diary weeks expand into sessions with ratios and durations', async ({ page }) => {
  await page.setViewportSize({ width: 1440, height: 900 });
  const errors = await open(page);

  const race = page.locator('.wrow', { has: page.getByText(/^31\sAug\s– /) });
  await race.getByRole('button').click();
  await expect(race.getByRole('button')).toHaveAttribute('aria-expanded', 'true');
  await expect(race.locator('.sessions')).toContainText('RACE_Run');
  await expect(race.locator('.sessions')).toContainText('4:00');
  await expect(race.locator('.sessions')).toContainText('47.6 km');
  // No running the week before: WoW is undefined, so it is left out rather than shown as 0.
  await expect(race.locator('.tail')).not.toContainText('WoW');

  const ride = page.locator('.wrow', { has: page.getByText(/^7–13\sSep$/) });
  await ride.getByRole('button').click();
  await expect(ride.locator('.tail')).toContainText('WoW 0.00×');
  await expect(ride.locator('.tail')).toContainText('ACWR 0.00');

  // Each guardrail flag is listed once, not once as a note and again as a flag.
  const big = page.locator('.wrow', { has: page.getByText(/^14–20\sSep$/) });
  await big.getByRole('button').click();
  await expect(big.locator('.verdict li.flag')).toHaveText([/R2.*ACWR/, /R6.*105 km/]);

  // The ledger names the same week by plan week and dates, ISO second, with its flags.
  const row = page.locator('.ledger tbody tr', { has: page.getByText('ISO W38', { exact: true }) });
  await expect(row.getByRole('rowheader')).toHaveText('W3 · 14–20 SepISO W38');
  await expect(row.locator('.chip')).toHaveText(['✕R2', '✕R6']);

  await noOverflow(page);
  expect(errors).toEqual([]);
});

test.describe('phone', () => {
  test.use({ viewport: { width: 390, height: 844 }, hasTouch: true, isMobile: true });

  test('bottom tabs switch sections without horizontal overflow', async ({ page }) => {
    const errors = await open(page);
    const tabs = page.getByRole('navigation', { name: 'Sections' });
    await expect(page.getByRole('heading', { name: 'This week' })).toBeVisible();
    await noOverflow(page);

    for (const [tab, heading] of [
      ['Diary', 'Weekly diary'],
      ['Plan', /-week plan/],
      ['History', 'Week ledger'],
      ['Today', 'This week'],
    ] as const) {
      await tabs.getByRole('link', { name: tab }).tap();
      await expect(tabs.getByRole('link', { name: tab })).toHaveAttribute('aria-current', 'page');
      await expect(page.getByRole('heading', { name: heading })).toBeVisible();
      await expect(page).toHaveURL(new RegExp(`#${tab.toLowerCase()}$`));
      await noOverflow(page);
    }
    await expect(page.getByRole('heading', { name: 'Week ledger' })).toHaveCount(0);

    // The tab lives in the URL: Back returns to the previous tab and a reload keeps it.
    await page.goBack();
    await expect(page.getByRole('heading', { name: 'Week ledger' })).toBeVisible();
    await page.reload();
    await expect(tabs.getByRole('link', { name: 'History' })).toHaveAttribute('aria-current', 'page');
    // Tapping the open tab again returns to its top rather than jumping to its anchor.
    // Plan has an element with its tab's id, so the browser's own jump would land on it.
    await tabs.getByRole('link', { name: 'Plan' }).tap();
    await page.evaluate(() => window.scrollTo(0, 600));
    await tabs.getByRole('link', { name: 'Plan' }).tap();
    await expect.poll(() => page.evaluate(() => window.scrollY)).toBe(0);

    // A closed diary week still shows its distance and climb.
    await tabs.getByRole('link', { name: 'Diary' }).tap();
    const race = page.locator('.wrow', { has: page.getByText(/^31\sAug\s– /) });
    await expect(race.getByRole('button')).toHaveAttribute('aria-expanded', 'false');
    await expect(race.locator('.wn').first()).toBeVisible();
    await expect(race.locator('.wn')).toHaveText(['70 km', '2,824 m']);
    expect(errors).toEqual([]);
  });
});
