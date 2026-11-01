import { DATA } from './data';
import { day, hm } from './format';

const range = (lo: number, hi: number | null) => (lo === 0 ? `≤ ${hi}` : hi === null ? `> ${lo}` : `${lo}–${hi}`);

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
      {phases.map(p => {
        const total = p.minutes.reduce((s, m) => s + m, 0);
        return (
          <div key={p.phase} className="zone-row">
            <div className="zone-label">
              <b>{p.phase}</b>{p.current && <span className="now-pill">now</span>}
              <span>{p.name}</span>
              <small>{day(p.start)} – {day(p.end)} · {hm(total / 60)} h{p.current ? ' so far' : ''}</small>
              {p.stream > 0 && <small>{Math.round((p.stream / total) * 100)}% from HR streams</small>}
            </div>
            <div>
              <div className="zone-bar" role="img"
                aria-label={bands.map((b, i) => `${b.code} ${hm(p.minutes[i] / 60)}`).join(', ')}>
                {p.minutes.map((m, i) => m > 0 && <i key={i} className={`z${i + 1}`} style={{ flexGrow: m }} />)}
              </div>
              <ol className="zone-vals">
                {p.minutes.map((m, i) => (
                  <li key={i} className={m ? '' : 'nil'}>
                    <b>{hm(m / 60)}</b><small>{total ? Math.round((m / total) * 100) : 0}%</small>
                  </li>
                ))}
              </ol>
            </div>
          </div>
        );
      })}
      <p className="caption">
        Runs with a fetched HR stream are split second by second; any other run counts whole in the zone of its
        average heart rate (COROS, else modelled from relative effort), which hides hard reps inside an easy
        session. Zones are Dan's Strava running zones.
        {phases.some(p => p.no_hr) ? ' Runs without any heart rate are left out.' : ''}
      </p>
    </section>
  );
}
