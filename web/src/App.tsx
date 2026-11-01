import { useEffect, useState } from 'react';
import { DATA } from './data';
import { Diary } from './Diary';
import { MON, current, curIdx, day, hm, lastRace, n, phaseShort, phaseSpans, plural, useWide } from './format';
import { Heatmap, Ledger } from './History';
import { PlanChart } from './Plan';
import { Fitness, Guardrails, ThisWeek } from './Week';
import { Zones } from './Zones';

const P = DATA.plan;

function Track() {
  const ph = curIdx >= 0 ? phaseSpans.find(s => curIdx >= s.a && curIdx <= s.b) : undefined;
  return (
    <div className="track">
      <p className="eyebrow">
        {curIdx >= 0 ? `Week ${curIdx + 1} of ${P.length}` : `${P.length}-week plan`}
        {ph && <span className="track-phase">{` · ${ph.phase} ${phaseShort(ph.name)}`}</span>}
      </p>
      <div className="track-row" style={{ gridTemplateColumns: `repeat(${P.length}, 1fr)` }}>
        {P.map((p, i) => (
          <i
            key={p.start}
            className={i < curIdx ? 'done' : i === curIdx ? 'cur' : p.race ? 'race' : ''}
            title={`W${p.index} · ${day(p.start)}${p.race ? ` · ${p.race}` : ''}`}
          />
        ))}
        {/* Phase codes and week ranges only: names did not fit and were cut off. */}
        {phaseSpans.map(s => (
          <span
            key={s.phase}
            className={curIdx >= s.a && curIdx <= s.b ? 'on' : ''}
            style={{ gridColumn: `${s.a + 1} / ${s.b + 2}` }}
            title={`${s.phase} ${s.name}`}
          >
            <b>{s.phase}</b>
            <small>
              {P[s.a].index}–{P[s.b].index}
            </small>
          </span>
        ))}
      </div>
    </div>
  );
}

/* When the page was built, against the viewer's clock: a stale page should say so. */
function Fresh() {
  // tl writes "01 November 2026, 18:02".
  const [d, mon, y] = DATA.generated.split(/[ ,]+/);
  const mi = MON.indexOf(mon.slice(0, 3));
  const now = new Date();
  const ago = Math.round((Date.UTC(now.getFullYear(), now.getMonth(), now.getDate()) - Date.UTC(+y, mi, +d)) / 864e5);
  // The build time carries no zone, so only the day is compared and shown.
  const when = ago <= 0 ? 'today' : ago === 1 ? 'yesterday' : `${+d} ${MON[mi]} · ${plural(ago, 'day')} ago`;
  const c = DATA.cache;
  return (
    <p
      className={`fresh${ago >= 3 ? ' stale' : ''}`}
      title={`Built ${DATA.generated} · ${n(c.n)} activities, ${day(c.first, true)} – ${day(c.last, true)}; last activity ${plural(c.stale, 'day')} before the build`}
    >
      <i aria-hidden="true" />
      Updated {when}
    </p>
  );
}

const GitHub = () => (
  <a className="repo" href="https://github.com/stancld/running-training-analysis" title="Source on GitHub">
    <svg viewBox="0 0 16 16" aria-hidden="true">
      <path d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27s1.36.09 2 .27c1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.01 8.01 0 0 0 16 8c0-4.42-3.58-8-8-8z" />
    </svg>
    <span>GitHub</span>
  </a>
);

function TopBar({ wide }: { wide: boolean }) {
  const weeks = Math.floor(DATA.race.weeks_to_go);
  if (!wide)
    return (
      <header className="topbar">
        <h1>Training Logbook</h1>
        <p className="race-line">
          <b>{weeks} weeks</b> to {DATA.race.name} · {day(DATA.race.date, true)}
        </p>
        <Fresh />
        <GitHub />
      </header>
    );
  return (
    <header className="topbar">
      <div className="brand">
        <h1>Training Logbook</h1>
        <p className="focus">
          <span>Current focus</span>
          {DATA.race.name} by UTMB · {day(DATA.race.date, true)}
        </p>
      </div>
      <Track />
      <div className="countdown">
        <b>{weeks} weeks</b>
        <span className="eyebrow">to the start line</span>
        <Fresh />
      </div>
      <GitHub />
    </header>
  );
}

/* A one-line note during race week only; afterwards the plan legend keeps the last race. */
function RaceWeek() {
  if (!lastRace || !current || lastRace.date < current.start) return null;
  return (
    <p className="race-line race-week">
      <span aria-hidden="true">▲</span> <b>{lastRace.name}</b> · {day(lastRace.date)} · {hm(lastRace.mins / 60)} ·{' '}
      {lastRace.km} km · {n(lastRace.vert)} m
    </p>
  );
}

const TABS = [
  ['today', 'Today', 'M3 10.5 12 3l9 7.5V21h-6v-6H9v6H3z'],
  ['plan', 'Plan', 'M4 5h16v15H4zM4 9h16M8 3v4M16 3v4'],
  ['diary', 'Diary', 'M12 6c-2-1.5-5-2-8-1.5V19c3-.5 6 0 8 1.5 2-1.5 5-2 8-1.5V4.5C17 4 14 4.5 12 6zM12 6v14.5'],
  ['history', 'History', 'M5 20V12M10 20V7M15 20v-9M20 20V4'],
] as const;
type Tab = (typeof TABS)[number][0];
// Every section has an anchor; on the phone it also names the tab that holds it.
const HOME: Record<string, Tab> = {
  today: 'today',
  rails: 'today',
  fitness: 'today',
  plan: 'plan',
  quality: 'plan',
  zones: 'plan',
  diary: 'diary',
  history: 'history',
  months: 'history',
  ledger: 'history',
};
const JUMP = [
  ['today', 'This week'],
  ['rails', 'Guardrails'],
  ['fitness', 'Fitness'],
  ['plan', 'Plan'],
  ['zones', 'HR zones'],
  ['diary', 'Diary'],
  ['months', 'Months'],
  ['ledger', 'Ledger'],
] as const;

/* Every hashchange counts, even to the same hash, so a repeated link still scrolls. */
function useHash() {
  const [nav, setNav] = useState(() => ({ hash: location.hash.slice(1), n: 0 }));
  useEffect(() => {
    const on = () => setNav(x => ({ hash: location.hash.slice(1), n: x.n + 1 }));
    addEventListener('hashchange', on);
    return () => removeEventListener('hashchange', on);
  }, []);
  return nav;
}

function Footer() {
  const c = DATA.cache;
  return (
    <footer>
      Built by <code>uv run tl site</code> on {DATA.generated} from {n(c.n)} activities ({day(c.first, true)} –{' '}
      {day(c.last, true)}). Weekly hours are moving time across all sports; heart rate is COROS-measured where
      available, otherwise estimated from Strava relative effort (±3.5 bpm).
    </footer>
  );
}

export default function App() {
  const wide = useWide();
  const nav = useHash(),
    hash = nav.hash;
  const tab: Tab = HOME[hash] ?? 'today';
  // Card popovers are fixed and would drift off their trigger, so any scroll closes it.
  useEffect(() => {
    const close = () => {
      for (const p of document.querySelectorAll<HTMLElement>('.tip:popover-open')) p.hidePopover();
    };
    addEventListener('scroll', close, { capture: true, passive: true });
    return () => removeEventListener('scroll', close, { capture: true });
  }, []);
  // After the tab renders: a tab opens at its top, a section anchor scrolls to it; nav.n
  // re-runs this for a repeated hash.
  useEffect(() => {
    if (!wide && (hash === tab || !hash)) window.scrollTo(0, 0);
    else if (hash) document.getElementById(hash === 'history' ? 'months' : hash)?.scrollIntoView();
  }, [nav.n, hash, tab, wide]);

  if (wide) {
    return (
      <div className="app wide">
        <TopBar wide />
        <nav className="jump" aria-label="Jump to">
          {JUMP.map(([id, label]) => (
            <a key={id} href={`#${id}`} aria-current={hash === id ? 'location' : undefined}>
              {label}
            </a>
          ))}
        </nav>
        <div className="row r1">
          <ThisWeek />
          <Guardrails />
          <Fitness />
        </div>
        <div className="row r2">
          <div className="stack">
            <PlanChart />
            <Zones />
          </div>
          <Diary />
        </div>
        <div className="row r3">
          <Heatmap />
          <Ledger />
        </div>
        <Footer />
      </div>
    );
  }
  return (
    <div className="app phone">
      <TopBar wide={false} />
      <main>
        {tab === 'today' && (
          <>
            <RaceWeek />
            <ThisWeek>
              <Guardrails inline />
            </ThisWeek>
            <Fitness compact />
          </>
        )}
        {tab === 'plan' && (
          <>
            <section className="card">
              <Track />
            </section>
            <PlanChart />
            <Zones />
          </>
        )}
        {tab === 'diary' && <Diary />}
        {tab === 'history' && (
          <>
            <Heatmap />
            <Ledger />
            <Footer />
          </>
        )}
      </main>
      <nav className="tabbar" aria-label="Sections">
        {TABS.map(([key, label, d]) => (
          <a
            key={key}
            href={`#${key}`}
            className={tab === key ? 'on' : ''}
            aria-current={tab === key ? 'page' : undefined}
            // The same tab again goes back to its top; the browser's own fragment jump would not.
            onClick={e => {
              if (hash !== key) return;
              e.preventDefault();
              window.scrollTo(0, 0);
            }}
          >
            <svg viewBox="0 0 24 24" aria-hidden="true">
              <path d={d} />
            </svg>
            {label}
          </a>
        ))}
      </nav>
    </div>
  );
}
