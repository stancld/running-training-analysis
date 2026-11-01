import { DATA } from './data';
import { day, hm } from './format';

const range = (lo: number, hi: number | null) => (lo === 0 ? `≤ ${hi}` : hi === null ? `> ${lo}` : `${lo}–${hi}`);

export function Zones() {
  const { bands, phases } = DATA.zones;
  if (!phases.length) return null;
  return (
    <section className="card zones" aria-labelledby="zones-h">
      <div className="ch">
        <h2 id="zones-h">Heart-rate zones by phase</h2>
        <span className="meta push">running time · by session average HR</span>
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
        Each run counts whole in the zone of its average heart rate (COROS, else modelled from relative effort),
        so hard reps inside an easy session are not separated. Zones are Dan's Strava running zones.
        {phases.some(p => p.no_hr) ? ' Runs without any heart rate are left out.' : ''}
      </p>
    </section>
  );
}
