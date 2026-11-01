import { useState } from 'react';
import { DATA, type Act, type DiaryWeek } from './data';
import { QUALITY, day, hm, n, phaseShort, raceOf, ratio, signed, span, tone } from './format';

const GLYPH: Record<string, string> = { bike: 'B', gym: 'G', hike: 'H', other: 'O' };
const glyph = (a: Act) => (a.group === 'run' ? (a.type === 'RACE' ? '▲' : (a.type ?? 'R')) : (GLYPH[a.group] ?? 'O'));

function Strip({ w }: { w: DiaryWeek }) {
  return (
    <ol className="strip" aria-label="Seven-day session strip">
      {w.days.map(d => {
        const a = d.acts.find(x => x.group === 'run') ?? d.acts[0];
        const cls = !a ? 'rest' : a.type === 'RACE' ? 'race' : a.group;
        return (
          <li key={d.date} className={cls}>
            <span>{d.day}</span>
            <b>{+d.date.slice(8)}</b>
            <i title={a ? `${d.acts.length} session${d.acts.length > 1 ? 's' : ''}` : 'Rest'}>{a ? glyph(a) : ''}</i>
          </li>
        );
      })}
    </ol>
  );
}

function Sessions({ w }: { w: DiaryWeek }) {
  return (
    <ul className="sessions">
      {w.days.map(d =>
        d.acts.length === 0 ? (
          <li key={d.date} className="rest">
            <span className="sd">
              {d.day} <em>{day(d.date)}</em>
            </span>
            <span className="sn">Rest</span>
          </li>
        ) : (
          d.acts.map((a, i) => (
            <li key={`${d.date}-${i}`} className={a.group}>
              <span className="sd">
                {i === 0 && (
                  <>
                    {d.day} <em>{day(d.date)}</em>
                  </>
                )}
              </span>
              <span className="sn">
                {a.type && <span className={`type${QUALITY.has(a.type) ? ' q' : ''}`}>{a.type}</span>}
                <b>{a.name || a.sport}</b>
                {a.feel != null && (
                  <small>
                    {' '}
                    feel {a.feel > 0 ? '+' : ''}
                    {a.feel}
                  </small>
                )}
                {a.note && <q>{a.note}</q>}
              </span>
              <span className="sv">{hm(a.mins / 60)}</span>
              <span className="sv">{a.km ? `${a.km.toFixed(1)} km` : ''}</span>
              <span className="sv">{a.vert ? `${n(a.vert)} m` : ''}</span>
            </li>
          ))
        ),
      )}
    </ul>
  );
}

function WeekRow({ w }: { w: DiaryWeek }) {
  const [open, setOpen] = useState(w.current);
  const p = w.plan,
    race = raceOf(w),
    t = tone(w);
  const r = p?.run_h ? w.run_h / p.run_h : null;
  const sessions = w.days.reduce((s, d) => s + d.acts.length, 0);
  const tail = [
    p ? `plan ${p.run_h} h run · ${p.bike_h} h bike · ${p.gym_h} h gym · weekend ${p.weekend}` : '',
    `bike ${w.bike_h.toFixed(1)} h · gym ${w.gym_h.toFixed(1)} h`,
    w.ctl !== null && w.atl !== null && w.tsb !== null
      ? `CTL ${w.ctl.toFixed(0)} · ATL ${w.atl.toFixed(0)} · form ${signed(w.tsb)}`
      : '',
    w.monotony ? `monotony ${w.monotony.toFixed(2)}` : '',
    w.wow != null ? `WoW ${ratio(w.wow, 2, '×')}` : '',
    w.acwr != null ? `ACWR ${ratio(w.acwr)}` : '',
    `${w.run_days} run days · ${w.rest_days} full rest`,
  ].filter(Boolean);
  return (
    <li className={`wrow${open ? ' open' : ''}${w.current ? ' cur' : ''}`}>
      <button type="button" className="wsum" aria-expanded={open} onClick={() => setOpen(!open)}>
        <span className="wk">{p ? `W${p.index}` : 'W0'}</span>
        <span className="wd">
          <b>{span(w.start, w.end)}</b>
          <span className={race ? 'race' : ''}>
            {race ? `Race · ${race.name}` : p ? `${p.phase} ${phaseShort(p.phase_name)}` : 'Lead-in'}
          </span>
        </span>
        <span className="wh">
          <b>
            {w.run_h.toFixed(1)}
            {p ? ` / ${p.run_h.toFixed(1)}` : ''} h
          </b>
          {r !== null && (
            <span className="bar">
              <i className={r > 1.15 ? 'over' : ''} style={{ width: `${Math.min(100, r * 100)}%` }} />
            </span>
          )}
        </span>
        <span className="wn">{Math.round(w.run_km)} km</span>
        <span className="wn">{n(w.run_vert)} m</span>
        <span className="wn ws">{sessions} sessions</span>
        <i
          role="img"
          className={`dot ${t}`}
          aria-label={t === 'ok' ? 'on target' : t === 'bad' ? 'guardrail flag' : 'off target'}
        />
        <span className="chev" aria-hidden="true" />
      </button>
      {open && (
        <div className="wbody">
          <Strip w={w} />
          <Sessions w={w} />
          <ul className="verdict">
            {!p && <li>Lead-in — the week before the macrocycle</li>}
            {w.notes.map((t2, i) => (
              <li key={i} className={t2.startsWith('[') ? 'flag' : ''}>
                {t2}
              </li>
            ))}
            {w.flags.map(f => (
              <li key={f.code} className="flag">
                {f.code} {f.msg}
              </li>
            ))}
          </ul>
          <div className="tail">
            {tail.map(s => (
              <span key={s}>{s}</span>
            ))}
          </div>
        </div>
      )}
    </li>
  );
}

export function Diary() {
  const weeks = DATA.diary.slice().reverse();
  return (
    <section className="card diary" aria-labelledby="diary-h">
      <div className="ch">
        <h2 id="diary-h">Weekly diary</h2>
        <span className="meta push">{weeks.length} weeks · newest first</span>
      </div>
      <p className="intro">
        Open a week for its sessions. Every line is derived from the cache; the quotes are Dan's own session notes.
      </p>
      {weeks.length ? (
        <ul className="wlist">
          {weeks.map(w => (
            <WeekRow key={w.start} w={w} />
          ))}
        </ul>
      ) : (
        <p className="caption">No weeks in the macrocycle yet.</p>
      )}
    </section>
  );
}
