import { useEffect, useState } from 'react';
import { DATA, type DiaryWeek } from './data';

export const MON = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
export const QUALITY = new Set(['T', 'I', 'R', 'M', 'F', 'RACE']);

// Round once, to whole minutes, then split — rounding hours and minutes separately gives 1:60.
export const hm = (h: number) => {
  const m = Math.round(h * 60);
  return `${Math.floor(m / 60)}:${String(m % 60).padStart(2, '0')}`;
};
export const day = (iso: string, year = false) =>
  new Date(iso).toLocaleDateString('en-GB', year
    ? { day: 'numeric', month: 'short', year: 'numeric' } : { day: 'numeric', month: 'short' });
export const span = (a: string, b: string) => `${day(a)} – ${day(b, true)}`;
export const phaseShort = (name: string) => name.split('—')[0].trim();
export const signed = (v: number) => `${v > 0 ? '+' : ''}${v.toFixed(0)}`;
export const n = (v: number) => v.toLocaleString('en-GB');
// WoW and ACWR are null when there is no prior load; 0 is a real ratio, so test for null only.
export const ratio = (v: number | null, digits = 2, unit = '') => (v != null ? `${v.toFixed(digits)}${unit}` : '—');

// Mirrors tl/diary.py: within ±15% of the target counts as on target.
export const offTarget = (w: DiaryWeek) => !!w.plan?.run_h && Math.abs(w.run_h / w.plan.run_h - 1) > 0.15;
export const raceOf = (w: DiaryWeek) =>
  w.days.flatMap(d => d.acts.filter(a => a.type === 'RACE').map(a => ({ ...a, date: d.date })))[0];
export const tone = (w: DiaryWeek) =>
  w.flags.some(f => f.code !== '--') ? 'bad' : (w.flags.length || offTarget(w)) ? 'watch' : 'ok';

export const current = DATA.diary.find(w => w.current) ?? DATA.diary[DATA.diary.length - 1];

export type Status = 'ok' | 'watch' | 'bad';
export type Rail = { code: string; value: string; rule: string; status: Status; why: string; history: Status[] };

/* Status comes from tl's own flags; "watch" marks a value past the line on a week the
   rule does not cover (R3 binds only above the big-week threshold). */
export function rails(): Rail[] {
  const w = current, G = DATA.guardrails;
  if (!w) return [];
  const flag = Object.fromEntries(w.flags.map(f => [f.code, f.msg]));
  const hist = DATA.weeks.slice(-6);
  const past = (code: string, watch?: (x: (typeof hist)[number]) => boolean): Status[] =>
    hist.map(x => (x.flags.includes(code) ? 'bad' : watch?.(x) ? 'watch' : 'ok'));
  const low = w.density < G.vert_floor;
  const rows: [string, string, string, string, Status[]][] = [
    ['R1', ratio(w.wow, 2, '×'), `WoW ≤ ${G.wow}×`, '', past('R1')],
    ['R2', ratio(w.acwr), `ACWR ≤ ${G.acwr.toFixed(2)}`, '', past('R2')],
    ['R3', `${w.density} m/h`, `≥ ${G.vert_floor} m/h over ${G.big_week_h} h`,
      low ? `${w.run_h.toFixed(1)} h week — the floor binds above ${G.big_week_h} h` : '',
      past('R3', x => x.density < G.vert_floor)],
    ['R4', flag.R4 ? 'Yes' : 'None', 'flat I/R work', '', past('R4')],
    ['R6', `${Math.round(w.run_km)} km`, `≤ ${G.km} km`, '', past('R6')],
  ];
  return rows.map(([code, value, rule, watch, history]) => ({
    code, value, rule, history,
    status: flag[code] ? 'bad' : watch ? 'watch' : 'ok',
    why: `${code}: ${flag[code] || watch || 'within the guardrail'}`,
  }));
}

export function useWide() {
  const q = '(min-width: 1024px)';
  const [wide, setWide] = useState(() => matchMedia(q).matches);
  useEffect(() => {
    const m = matchMedia(q), on = () => setWide(m.matches);
    m.addEventListener('change', on);
    return () => m.removeEventListener('change', on);
  }, []);
  return wide;
}
