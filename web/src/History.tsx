import { useState } from 'react';
import { DATA } from './data';
import { MON, hm, n, ratio } from './format';

const byKey = Object.fromEntries(DATA.months.map(m => [m.label, m]));
const years = [...new Set(DATA.months.map(m => +m.label.slice(0, 4)))].reverse();
const step = (h: number) => (h === 0 ? 0 : h < 10 ? 1 : h < 18 ? 2 : h < 26 ? 3 : h < 33 ? 4 : 5);
const RAMP: [string, number][] = [['0', 0], ['<10', 1], ['10–18', 2], ['18–26', 3], ['26–33', 4], ['33+', 5]];

export function Heatmap() {
  const nowKey = DATA.today.slice(0, 7);
  const [sel, setSel] = useState(nowKey);
  const m = byKey[sel];
  return (
    <section className="card heat" aria-labelledby="map-h">
      <div className="ch">
        <h2 id="map-h">Every month since {years[years.length - 1]}</h2>
        <span className="meta push">run hours per month</span>
      </div>
      <p className="intro">The gaps are the injuries: February–March 2024, April 2025, and the two months the January 2026 calf cost. Hover or tap a month.</p>
      <div className="mapgrid">
        <span />
        {MON.map(x => <span key={x} className="hd">{x}</span>)}
        {years.map(y => [
          <span key={y} className="yr">{y}</span>,
          ...MON.map((_, i) => {
            const key = `${y}-${String(i + 1).padStart(2, '0')}`, mm = byKey[key], k = step(mm ? mm.run_h : 0);
            return (
              <button key={key} className={`cell${key === nowKey ? ' now' : ''}${key === sel ? ' sel' : ''}`}
                style={{ background: `var(--s${k})`, color: `var(--on-s${k})` }} aria-label={key}
                onPointerEnter={e => e.pointerType === 'mouse' && setSel(key)} onClick={() => setSel(key)}>
                {mm && <><b>{mm.run_h.toFixed(0)}</b><i>{Math.round(mm.run_km)} km</i></>}
              </button>
            );
          }),
        ])}
      </div>
      <div className="ramp">
        {RAMP.map(([l, k]) => <span key={l}><i style={{ background: `var(--s${k})` }} />{l} h</span>)}
        <span>· garnet outline: this month</span>
      </div>
      <div className="week-detail" aria-live="polite">
        <b>{sel}</b>
        {m ? <>
          <span>{m.run_h.toFixed(1)} h run · {m.run_km.toFixed(0)} km · {n(m.run_vert)} m · {m.density} m/h</span>
          <span>{m.run_days} run days · longest {hm(m.longest / 60)} · {m.quality} quality · feel {m.feel === null ? '—' : `${m.feel > 0 ? '+' : ''}${m.feel.toFixed(1)}`}</span>
          <span>bike {m.bike_h.toFixed(1)} h · gym {m.gym_h.toFixed(1)} h · total {m.total_h.toFixed(1)} h</span>
          {m.hr !== null && m.pace !== null && <span>easy/long HR {m.hr.toFixed(0)} bpm at {hm(m.pace)} /km</span>}
        </> : <span>nothing recorded</span>}
      </div>
    </section>
  );
}

export function Ledger() {
  const planBy = Object.fromEntries(DATA.plan.map(p => [p.start, p]));
  const rows = DATA.weeks.slice(-26).reverse();
  return (
    <section className="card ledger" aria-labelledby="ledger-h">
      <div className="ch">
        <h2 id="ledger-h">Week ledger</h2>
        <span className="meta push">last {rows.length} weeks</span>
      </div>
      <p className="intro">Every week scored against the guardrails. WoW and ACWR are running hours only — the bike carries load the tendons never see.</p>
      <div className="tw">
        <table>
          <thead><tr>
            <th>Week</th><th className="n">Run h</th><th className="n">Plan</th><th className="n">km</th>
            <th className="n">Vert</th><th className="n">m/h</th><th className="n">Bike</th><th className="n">Gym</th>
            <th className="n">Total</th><th className="n">WoW</th><th className="n">ACWR</th><th>Rails</th>
          </tr></thead>
          <tbody>
            {rows.map(w => {
              const p = planBy[w.start];
              return (
                <tr key={w.start} className={w.current ? 'now' : w.flags.length ? 'flagged' : ''}>
                  <td className="mono" title={`Monday ${w.start}`}>{w.label}</td>
                  <td className="n">{w.run_h.toFixed(1)}</td><td className="n">{p ? p.run_h.toFixed(1) : '—'}</td>
                  <td className="n">{w.km.toFixed(0)}</td><td className="n">{n(w.vert)}</td>
                  <td className="n">{w.density}</td><td className="n">{w.bike_h.toFixed(1)}</td>
                  <td className="n">{w.gym_h.toFixed(1)}</td><td className="n">{w.total_h.toFixed(1)}</td>
                  <td className="n">{ratio(w.wow)}</td><td className="n">{ratio(w.acwr)}</td>
                  <td>{w.flags.length ? w.flags.map(f => <span key={f} className="chip bad">{f}</span>)
                    : <span className="chip ok">ok</span>}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
      <p className="note"><b>Flags.</b> <span className="chip bad">R1</span> WoW jump above {DATA.guardrails.wow}×, the strongest
        injury predictor in the record. <span className="chip bad">R2</span> ACWR above {DATA.guardrails.acwr.toFixed(2)}.{' '}
        <span className="chip bad">R3</span> over {DATA.guardrails.big_week_h} h below {DATA.guardrails.vert_floor} m/h — flat volume.{' '}
        <span className="chip bad">R6</span> over {DATA.guardrails.km} km. R4 fires only for <em>flat</em> I/R work.</p>
    </section>
  );
}
