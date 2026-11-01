import { useState } from 'react';
import { DATA, type PhaseZones, type ZoneBand } from './data';
import { day, hm } from './format';

const range = (lo: number, hi: number | null) => (lo === 0 ? `≤ ${hi}` : hi === null ? `> ${lo}` : `${lo}–${hi}`);

const pct = (m: number, total: number) => (total ? Math.round((m / total) * 100) : 0);

function Bar({ minutes, bands, thin = false }: { minutes: number[]; bands: ZoneBand[]; thin?: boolean }) {
  return (
    <div className={`zone-bar${thin ? ' thin' : ''}`} role="img"
      aria-label={bands.map((b, i) => `${b.code} ${hm(minutes[i] / 60)}`).join(', ')}>
      {minutes.map((m, i) => m > 0 && <i key={i} className={`z${i + 1}`} style={{ flexGrow: m }} />)}
    </div>
  );
}

function PhaseRow({ p, bands }: { p: PhaseZones; bands: ZoneBand[] }) {
  const [open, setOpen] = useState(p.current);
  const total = p.minutes.reduce((s, m) => s + m, 0);
  return (
    <div className={`zone-phase${open ? ' open' : ''}`}>
      <div className="zone-row">
        <div className="zone-label">
          <b>{p.phase}</b>{p.current && <span className="now-pill">now</span>}
          <span>{p.name}</span>
          <small>{day(p.start)} – {day(p.end)} · {hm(total / 60)} h{p.current ? ' so far' : ''}</small>
          {p.stream > 0 && <small>{pct(p.stream, total)}% from HR streams</small>}
        </div>
        <div>
          <Bar minutes={p.minutes} bands={bands} />
          <ol className="zone-vals">
            {p.minutes.map((m, i) => (
              <li key={i} className={m ? '' : 'nil'}><b>{hm(m / 60)}</b><small>{pct(m, total)}%</small></li>
            ))}
          </ol>
        </div>
      </div>
      {p.weeks.length > 0 && (
        <button className="zone-toggle" aria-expanded={open} onClick={() => setOpen(!open)}>
          <span className="chev" aria-hidden="true" />
          {open ? 'Hide' : 'Show'} {p.weeks.length} week{p.weeks.length > 1 ? 's' : ''}
        </button>
      )}
      {open && (
        <ul className="zone-weeks">
          {p.weeks.map(w => {
            const wt = w.minutes.reduce((s, m) => s + m, 0);
            return (
              <li key={w.start} className={w.current ? 'cur' : ''}>
                <span className="zw-label"><b>W{w.index}</b>{day(w.start)} – {day(w.end)}</span>
                {wt ? <Bar minutes={w.minutes} bands={bands} thin /> : <span className="zw-none">no running</span>}
                <span className="zw-vals">
                  {wt > 0 && <span>{hm(wt / 60)} h</span>}
                  {wt > 0 && w.minutes.map((m, i) => pct(m, wt) > 0 && <span key={i}>{bands[i].code} {pct(m, wt)}%</span>)}
                </span>
              </li>
            );
          })}
        </ul>
      )}
    </div>
  );
}

export function Zones() {
  const { bands, phases } = DATA.zones;
  if (!phases.length) return null;
  const run = phases.reduce((s, p) => s + p.stream + p.measured + p.modelled, 0);
  const share = run ? Math.round((phases.reduce((s, p) => s + p.stream, 0) / run) * 100) : 0;
  return (
    <section className="card zones" aria-labelledby="zones-h">
      <div className="ch">
        <h2 id="zones-h">Heart-rate zones by phase</h2>
        <span className="meta push">running time · {share ? `${share}% from HR streams` : 'by session average HR'}</span>
      </div>
      <ul className="zone-key">
        {bands.map((b, i) => (
          <li key={b.code}><i className={`z${i + 1}`} /><span><b>{b.code}</b> {b.name}<small>{range(b.lo, b.hi)} bpm</small></span></li>
        ))}
      </ul>
      {phases.map(p => <PhaseRow key={p.phase} p={p} bands={bands} />)}
      <p className="caption">
        Runs with a fetched HR stream are split second by second; any other run counts whole in the zone of its
        average heart rate (COROS, else modelled from relative effort), which hides hard reps inside an easy
        session. Zones are Dan's Strava running zones.
        {phases.some(p => p.no_hr) ? ' Runs without any heart rate are left out.' : ''}
      </p>
    </section>
  );
}
