import { useEffect, useRef, useState } from 'react';
import { DATA, type DiaryWeek, type LedgerWeek } from './data';

export const MON = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
export const QUALITY = new Set(['T', 'I', 'R', 'M', 'F', 'RACE']);

// Round once, to whole minutes, then split — rounding hours and minutes separately gives 1:60.
export const hm = (h: number) => {
  const m = Math.round(h * 60);
  return `${Math.floor(m / 60)}:${String(m % 60).padStart(2, '0')}`;
};
// A bare 'YYYY-MM-DD' parses as UTC midnight, so it is read in UTC or viewers west of
// Greenwich see the day before. Months come from MON: en-GB Intl writes "Sept".
export const day = (iso: string, year = false) => {
  const d = new Date(iso);
  return `${d.getUTCDate()} ${MON[d.getUTCMonth()]}${year ? ` ${d.getUTCFullYear()}` : ''}`;
};
export const addDays = (iso: string, k: number) => {
  const d = new Date(iso);
  d.setUTCDate(d.getUTCDate() + k);
  return d.toISOString().slice(0, 10);
};
// "19–25 Oct" inside a month, "28 Sep – 4 Oct" across one; non-breaking inside each date.
const nb = (s: string) => s.replaceAll(' ', '\u00a0');
export const span = (a: string, b: string, year = false) =>
  a.slice(0, 7) === b.slice(0, 7)
    ? nb(`${+a.slice(8)}–${day(b, year)}`)
    : `${nb(day(a, year && a.slice(0, 4) !== b.slice(0, 4)))}\u00a0– ${nb(day(b, year))}`;
// '2026-11' → 'Nov 2026'
export const month = (key: string) => `${MON[+key.slice(5, 7) - 1]} ${key.slice(0, 4)}`;
export const phaseShort = (name: string) => name.split('—')[0].trim();
export const signed = (v: number) => `${v > 0 ? '+' : ''}${v.toFixed(0)}`;
export const n = (v: number) => v.toLocaleString('en-GB');
export const plural = (k: number, one: string, many = `${one}s`) => `${k} ${k === 1 ? one : many}`;
// WoW and ACWR are null when there is no prior load; 0 is a real ratio, so test for null only.
export const ratio = (v: number | null, digits = 2, unit = '') => (v != null ? `${v.toFixed(digits)}${unit}` : '—');

/* Weeks are named by the plan (W1–W29) wherever the plan covers them, with their dates;
   the ISO week is secondary, for matching the terminal output. */
const planBy = Object.fromEntries(DATA.plan.map(p => [p.start, p]));
export const planWeek = (start: string) => (planBy[start] ? `W${planBy[start].index}` : null);
export const isoWeek = (iso: string) => {
  const d = new Date(iso);
  d.setUTCDate(d.getUTCDate() + 3 - ((d.getUTCDay() + 6) % 7));
  const jan4 = new Date(Date.UTC(d.getUTCFullYear(), 0, 4));
  return `ISO W${1 + Math.round(((+d - +jan4) / 864e5 - 3 + ((jan4.getUTCDay() + 6) % 7)) / 7)}`;
};
export const weekTitle = (start: string) =>
  [planWeek(start), span(start, addDays(start, 6), true), isoWeek(start)].filter(Boolean).join(' · ');

// Mirrors tl/diary.py: within ±15% of the target counts as on target.
const offTarget = (w: DiaryWeek) => !!w.plan?.run_h && Math.abs(w.run_h / w.plan.run_h - 1) > 0.15;
export const raceOf = (w: DiaryWeek) =>
  w.days.flatMap(d => d.acts.filter(a => a.type === 'RACE').map(a => ({ ...a, date: d.date })))[0];
/* A diary week's status and why: tl's flags, then the same watches the guardrail card and
   ledger show ('--' is tl's Dec–Apr big-week advisory), then the plan comparison. */
export function tone(w: DiaryWeek): [Status, string] {
  const codes = w.flags.map(f => f.code);
  const hard = codes.filter(c => c !== '--');
  if (hard.length) return ['flag', `guardrail flagged: ${hard.join(', ')}`];
  const why = [
    codes.includes('--') ? 'big week in the Dec–Apr window' : '',
    r3Watch({ start: w.start, flags: codes, run_h: w.run_h, density: w.density })
      ? `R3 ${w.density} m/h, under the floor`
      : '',
    offTarget(w) ? 'off target' : '',
  ].filter(Boolean);
  return why.length ? ['watch', why.join('; ')] : ['ok', 'on target'];
}

export const current = DATA.diary.find(w => w.current) ?? DATA.diary[DATA.diary.length - 1];
export const lastRace = DATA.diary.map(raceOf).filter(Boolean).pop();

// The plan as the top-bar track and the plan chart both draw it: this week's index and
// each phase's run of weeks.
export const curIdx = DATA.plan.findIndex(p => p.start === DATA.weeks.find(w => w.current)?.start);
export const phaseSpans: { phase: string; name: string; a: number; b: number }[] = [];
DATA.plan.forEach((p, i) => {
  const last = phaseSpans[phaseSpans.length - 1];
  if (last?.phase === p.phase) last.b = i;
  else phaseSpans.push({ phase: p.phase, name: p.phase_name, a: i, b: i });
});

// What each rule is and why it exists, after the README's guardrails table.
const G = DATA.guardrails;
export const GUARDRAIL: Record<string, [string, string]> = {
  R1: [
    'Week-over-week load',
    `This week's running hours over last week's, kept at or under ${G.wow}×. Sudden jumps are the strongest injury predictor in the record.`,
  ],
  R2: [
    'Acute:chronic load',
    `This week's running hours over the mean of the four weeks before it, kept at or under ${G.acwr.toFixed(2)}. The base built so far caps how fast load can rise.`,
  ],
  R3: [
    'Climb density',
    `Metres of climb per running hour, at least ${G.vert_floor} m/h on weeks over ${G.big_week_h} h. Flat volume is what drove the calf and shin injuries.`,
  ],
  R4: [
    'No flat intervals',
    'No flat interval or repetition sessions this season, so hard running stays off flat ground. Uphill reps are fine and are not flagged.',
  ],
  R6: ['Weekly distance cap', `At most ${G.km} km of running in a week, however the hours add up.`],
};

/* One vocabulary for the card, the phone list, the dots, the diary and the ledger:
   ok, watch (worth a look, not a breach) and flag (a guardrail tl flagged). */
export type Status = 'ok' | 'watch' | 'flag';
export const MARK: Record<Status, string> = { ok: '✓', watch: '!', flag: '✕' };
// tl flags R3 only on big weeks; below the floor on a smaller running week is a watch.
// tl scores no week still in progress, so neither does the watch.
const PARTIAL = new Set(DATA.diary.filter(w => w.partial).map(w => w.start));
export const r3Watch = (x: { start: string; flags: string[]; run_h: number; density: number }) =>
  !PARTIAL.has(x.start) && !x.flags.includes('R3') && x.run_h > 0 && x.density < G.vert_floor;
export const watchNote = (x: { run_h: number }) =>
  `Below the ${G.vert_floor} m/h floor; it binds only over ${G.big_week_h} h (a ${x.run_h.toFixed(1)} h week)`;

export type RailWeek = { status: Status; week: string; dates: string; value: string; note: string; current: boolean };
export type Rail = {
  code: string;
  name: string;
  value: string;
  rule: string;
  status: Status;
  note: string;
  history: RailWeek[];
};

/* Status comes from tl's own flags; the only watch is R3 under the floor on a week the
   rule does not cover. */
export function rails(): Rail[] {
  const w = current;
  if (!w) return [];
  const flag = Object.fromEntries(w.flags.map(f => [f.code, f.msg]));
  const hist = DATA.weeks.slice(-6);
  const past = (code: string, value: (x: LedgerWeek) => string): RailWeek[] =>
    hist.map(x => {
      const status: Status = x.flags.includes(code) ? 'flag' : code === 'R3' && r3Watch(x) ? 'watch' : 'ok';
      return {
        status,
        week: [planWeek(x.start), isoWeek(x.start)].filter(Boolean).join(' · '),
        dates: span(x.start, addDays(x.start, 6)),
        value: value(x),
        note: { ok: 'Within the guardrail', watch: watchNote(x), flag: 'Guardrail flagged' }[status],
        current: x.current,
      };
    });
  const r3 = { start: w.start, flags: w.flags.map(f => f.code), run_h: w.run_h, density: w.density };
  const rows: [string, string, string, RailWeek[]][] = [
    ['R1', ratio(w.wow, 2, '×'), `≤ ${G.wow}×`, past('R1', x => ratio(x.wow, 2, '×'))],
    ['R2', ratio(w.acwr), `≤ ${G.acwr.toFixed(2)}`, past('R2', x => ratio(x.acwr))],
    [
      'R3',
      `${w.density} m/h`,
      `≥ ${G.vert_floor} m/h over\u00a0${G.big_week_h}\u00a0h`,
      past('R3', x => `${x.density} m/h · ${x.run_h.toFixed(1)} h`),
    ],
    [
      'R4',
      flag.R4 ? 'logged' : 'clear',
      'flat I/R work',
      past('R4', x => (x.flags.includes('R4') ? 'logged' : 'clear')),
    ],
    ['R6', `${Math.round(w.run_km)} km`, `≤ ${G.km} km`, past('R6', x => `${Math.round(x.km)} km`)],
  ];
  return rows.map(([code, value, rule, history]) => {
    const status: Status = flag[code] ? 'flag' : code === 'R3' && r3Watch(r3) ? 'watch' : 'ok';
    return {
      code,
      name: GUARDRAIL[code][0],
      value,
      rule,
      history,
      status,
      note: status === 'flag' ? flag[code] : status === 'watch' ? watchNote(w) : '',
    };
  });
}

export function useWide() {
  const q = '(min-width: 1024px)';
  const [wide, setWide] = useState(() => matchMedia(q).matches);
  useEffect(() => {
    const m = matchMedia(q),
      on = () => setWide(m.matches);
    m.addEventListener('change', on);
    return () => m.removeEventListener('change', on);
  }, []);
  return wide;
}

/* An SVG scales with its column, so its type would too (0.7× on a small phone, 2× on a
   tablet). Charts measure their rendered width and size labels from it. */
export function useRenderedWidth<T extends Element>(initial: number) {
  const ref = useRef<T>(null);
  const [px, setPx] = useState(initial);
  useEffect(() => {
    const ro = new ResizeObserver(([e]) => e.contentRect.width && setPx(e.contentRect.width));
    if (ref.current) ro.observe(ref.current);
    return () => ro.disconnect();
  }, []);
  return [ref, px] as const;
}
