import { useState } from 'react';
import { DATA, type PhaseZones, type WeekZones, type ZoneBand, type ZoneSplit } from './data';
import { hm, span } from './format';

type Mode = 'run' | 'total';
type Split = { run: ZoneSplit; bike: ZoneSplit };

const range = (lo: number, hi: number | null) => (lo === 0 ? `≤ ${hi}` : hi === null ? `> ${lo}` : `${lo + 1}–${hi}`);
const pct = (m: number, total: number) => (total ? Math.round((m / total) * 100) : 0);
const sum = (xs: number[]) => xs.reduce((s, x) => s + x, 0);
// Total adds runs and rides zone by zone; each sport keeps its own limits (Strava running, Garmin cycling).
const hrMinutes = (z: Split, mode: Mode) =>
  mode === 'run' ? z.run.minutes : z.run.minutes.map((m, i) => m + z.bike.minutes[i]);
const parts = (zs: Split[], mode: Mode) => zs.flatMap(z => (mode === 'run' ? [z.run] : [z.run, z.bike]));
const streamShare = (ps: ZoneSplit[]) =>
  pct(sum(ps.map(p => p.stream)), sum(ps.map(p => p.stream + p.measured + p.modelled)));

function Key({ title, bands, kind, unit }: { title: string; bands: ZoneBand[]; kind: 'z' | 'p'; unit: string }) {
  return (
    <div className="key-group">
      <p>
        {title} <small>({unit})</small>
      </p>
      <ul>
        {bands.map((b, i) => (
          <li key={b.code}>
            <span>
              <i className={`${kind}${i + 1}`} />
              {b.code}
            </span>
            <small>{range(b.lo, b.hi)}</small>
          </li>
        ))}
      </ul>
    </div>
  );
}

function Breakdown({
  title,
  meta,
  minutes,
  bands,
  kind,
}: {
  title: string;
  meta?: string;
  minutes: number[];
  bands: ZoneBand[];
  kind: 'z' | 'p';
}) {
  const total = sum(minutes);
  return (
    <div className="breakdown">
      <p className="zone-sub">
        <b>{title}</b>
        {meta && <> · {meta}</>}
      </p>
      <div
        className="zone-bar"
        role="img"
        aria-label={bands.map((b, i) => `${b.code} ${hm(minutes[i] / 60)}`).join(', ')}
      >
        {minutes.map((m, i) => m > 0 && <i key={i} className={`${kind}${i + 1}`} style={{ flexGrow: m }} />)}
      </div>
      <ol className="zone-vals" style={{ gridTemplateColumns: `repeat(${minutes.length}, minmax(0,1fr))` }}>
        {minutes.map((m, i) => (
          <li key={i} className={m ? '' : 'nil'}>
            <span>
              <i className={`${kind}${i + 1}`} />
              {bands[i].code}
            </span>
            <b>{hm(m / 60)}</b>
            <small>{pct(m, total)}%</small>
          </li>
        ))}
      </ol>
    </div>
  );
}

function WeekColumns({ weeks, mode }: { weeks: WeekZones[]; mode: Mode }) {
  const { bands } = DATA.zones;
  const rows = weeks.map(w => ({ w, m: hrMinutes(w, mode) }));
  const top = Math.max(1, ...rows.map(r => sum(r.m)));
  return (
    <div className="zone-cols" style={{ gridTemplateColumns: `repeat(${Math.max(rows.length, 4)}, minmax(0,1fr))` }}>
      {rows.map(({ w, m }) => {
        const t = sum(m);
        const label =
          `W${w.index} · ${span(w.start, w.end)}: ${hm(t / 60)} h` +
          (t
            ? `, ${m
                .map((x, i) => (pct(x, t) ? `${bands[i].code} ${pct(x, t)}%` : ''))
                .filter(Boolean)
                .join(', ')}`
            : '');
        return (
          <div
            key={w.start}
            className={`zone-col${w.current ? ' cur' : ''}`}
            role="img"
            aria-label={label}
            title={label}
          >
            <b>{t ? hm(t / 60) : '—'}</b>
            <div className="col-track">
              <div className="col-stack" style={{ height: `${(t / top) * 100}%` }}>
                {m.map((x, i) => x > 0 && <i key={i} className={`z${i + 1}`} style={{ flexGrow: x }} />)}
              </div>
            </div>
            <span>W{w.index}</span>
          </div>
        );
      })}
    </div>
  );
}

function PhaseRow({ p, mode }: { p: PhaseZones; mode: Mode }) {
  const { bands, power_bands } = DATA.zones;
  const [open, setOpen] = useState(p.current);
  const hr = hrMinutes(p, mode),
    total = sum(hr),
    share = streamShare(parts([p], mode));
  const watts = sum(p.bike.power);
  return (
    <div className={`zone-phase${open ? ' open' : ''}`}>
      <div className="zone-row">
        <div className="zone-label">
          <b>{p.phase}</b>
          {p.current && <span className="now-pill">now</span>}
          <span>{p.name}</span>
          <small>
            {span(p.start, p.end)} · {hm(total / 60)} h{p.current ? ' so far' : ''}
          </small>
          {share > 0 && <small>{share}% from HR streams</small>}
        </div>
        <div className="zone-main">
          <Breakdown
            title={mode === 'run' ? 'Time in run HR zones' : 'Time in all HR zones'}
            meta={mode === 'run' ? undefined : 'run + ride'}
            minutes={hr}
            bands={bands}
            kind="z"
          />
          {mode === 'total' &&
            (watts > 0 ? (
              <Breakdown
                title="Time in ride power zones"
                meta={`${hm(watts / 60)} h with watts`}
                minutes={p.bike.power}
                bands={power_bands}
                kind="p"
              />
            ) : (
              <p className="zone-none">No ride power in this phase.</p>
            ))}
        </div>
      </div>
      {p.weeks.length > 0 && (
        <button type="button" className="zone-toggle" aria-expanded={open} onClick={() => setOpen(!open)}>
          <span className="chev" aria-hidden="true" />
          {open ? 'Hide' : 'Show'} {p.weeks.length} week{p.weeks.length > 1 ? 's' : ''}
        </button>
      )}
      {open && <WeekColumns weeks={p.weeks} mode={mode} />}
    </div>
  );
}

export function Zones() {
  const { bands, bike_bands, power_bands, phases } = DATA.zones;
  const [mode, setMode] = useState<Mode>('run');
  if (!phases.length) return null;
  const all = parts(phases, mode);
  const share = streamShare(all);
  const noHr = sum(all.map(p => p.no_hr));
  return (
    <section className="card zones" id="zones" aria-labelledby="zones-h">
      <div className="ch">
        <h2 id="zones-h">Heart-rate zones by phase</h2>
        <fieldset className="mode" aria-label="Sports">
          {(['run', 'total'] as const).map(m => (
            <button
              key={m}
              type="button"
              aria-pressed={mode === m}
              className={mode === m ? 'on' : ''}
              onClick={() => setMode(m)}
            >
              {m === 'run' ? 'Running' : 'Total'}
            </button>
          ))}
        </fieldset>
        <span className="meta push">
          {mode === 'run' ? 'running time' : 'running + riding'} ·{' '}
          {share ? `${share}% from HR streams` : 'by session average HR'}
        </span>
      </div>
      <div className={`zone-keys${mode === 'total' ? ' total' : ''}`}>
        <Key title="Run HR zones" bands={bands} kind="z" unit="bpm" />
        {mode === 'total' && <Key title="Ride HR zones" bands={bike_bands} kind="z" unit="bpm" />}
        {mode === 'total' && <Key title="Power zones" bands={power_bands} kind="p" unit="W" />}
      </div>
      {phases.map(p => (
        <PhaseRow key={p.phase} p={p} mode={mode} />
      ))}
      <details className="how">
        <summary>How it's computed</summary>
        <p>
          Activities with a fetched stream are split second by second; a run without one counts whole in the zone of its
          average heart rate (COROS, else modelled from relative effort). Running zones are Dan's Strava zones; rides
          use his Garmin HR and power zones, and Total adds the two sports zone by zone.
          {noHr
            ? ` ${hm(noHr / 60)} h without heart rate ${mode === 'total' ? '(rides without a strap still count in power) ' : ''}is left out of the HR bars.`
            : ''}
        </p>
      </details>
    </section>
  );
}
