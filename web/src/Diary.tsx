import { useState } from 'react';
import { DATA, type Act, type DiaryWeek } from './data';
import { MARK, QUALITY, day, hm, isoWeek, n, phaseShort, plural, raceOf, ratio, signed, span, tone } from './format';

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
                <b>{a.name || `${a.sport} session`}</b>
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
    [t, why] = tone(w);
  const r = p?.run_h ? w.run_h / p.run_h : null;
  // What the summary row and the sessions do not already say; cross-training appears only
  // when it was done or planned, as done / planned.
  const cross = (
    [
      ['bike', w.bike_h, p?.bike_h],
      ['gym', w.gym_h, p?.gym_h],
    ] as const
  )
    .filter(([, a, b]) => a || b)
    .map(([k, a, b]) => `${k} ${a.toFixed(1)}${b ? ` / ${b}` : ''} h`)
    .join(' · ');
  const tail = [
    p ? `Weekend plan: ${p.weekend}` : '',
    cross,
    `${plural(w.run_days, 'run day')} · ${w.rest_days} full rest`,
    w.wow != null ? `WoW ${ratio(w.wow, 2, '×')}` : '',
    w.acwr != null ? `ACWR ${ratio(w.acwr)}` : '',
    w.ctl !== null && w.atl !== null && w.tsb !== null
      ? `CTL ${w.ctl.toFixed(0)} · ATL ${w.atl.toFixed(0)} · form ${signed(w.tsb)}`
      : '',
    w.monotony ? `monotony ${w.monotony.toFixed(2)}` : '',
  ].filter(Boolean);
  return (
    <li className={`wrow${open ? ' open' : ''}${w.current ? ' cur' : ''}`}>
      <button type="button" className="wsum" aria-expanded={open} onClick={() => setOpen(!open)}>
        <span className="wk" title={isoWeek(w.start)}>
          {p ? `W${p.index}` : 'W0'}
        </span>
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
        <i role="img" className={`dot ${t}`} aria-label={`${t}: ${why}`} title={`${t} · ${why}`}>
          {MARK[t]}
        </i>
        <span className="chev" aria-hidden="true" />
      </button>
      {open && (
        <div className="wbody">
          <Strip w={w} />
          <Sessions w={w} />
          <ul className="verdict">
            {!p && <li>Lead-in — the week before the macrocycle</li>}
            {/* Notes already carry each guardrail flag as "[R1] …", as in the terminal diary. */}
            {w.notes.map((t2, i) => (
              <li key={i} className={t2.startsWith('[') ? 'flag' : ''}>
                {t2}
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
    <section className="card diary" id="diary" aria-labelledby="diary-h">
      <div className="ch">
        <h2 id="diary-h">Weekly diary</h2>
        <span className="meta push">{plural(weeks.length, 'week')} · newest first</span>
      </div>
      <p className="intro">Open a week for its sessions. The quotes are Dan's own notes; everything else is derived.</p>
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
