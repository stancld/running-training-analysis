import { useEffect, useState } from 'react';
import { DATA } from './data';
import { curIdx, day, lastRace, n, phaseShort, phaseSpans, useRenderedWidth, useWide, weekTitle } from './format';

const P = DATA.plan,
  PROV = DATA.provisional;
const actual = Object.fromEntries(DATA.weeks.map(w => [w.start, w]));

function detail(i: number) {
  const p = P[i],
    a = actual[p.start];
  const head = `${weekTitle(p.start)} · ${p.phase} ${phaseShort(p.phase_name)}`;
  if (p.committed) {
    return [
      head,
      `Plan ${p.run_h.toFixed(1)} h run${p.bike_h ? ` · ${p.bike_h.toFixed(1)} h bike` : ''}${p.gym_h ? ` · ${p.gym_h} h gym` : ''} · ${p.km} km · ${p.vert === null ? 'no vert target' : `${n(p.vert)} m`}`,
      a ? `Ran ${a.run_h.toFixed(1)} h · ${a.km} km · ${n(a.vert)} m · ${a.density} m/h` : 'Not run yet',
      p.race ?? `Weekend: ${p.weekend}`,
    ];
  }
  const q = PROV.find(x => x.phase === p.phase);
  return [
    head,
    'Provisional: the phase carries a band, not a weekly number',
    q
      ? `Run ${q.run_h[0].toFixed(1)}–${q.run_h[1].toFixed(1)} h/wk · bike ${q.bike_h[0].toFixed(1)}–${q.bike_h[1].toFixed(1)} h/wk`
      : '',
    q
      ? `${q.km[0]}–${q.km[1]} km · ${n(q.vert[0])}–${n(q.vert[1])} m · phase ${n(q.total_km)} km over ${q.weeks} wk`
      : '',
    p.race ?? '',
  ].filter(Boolean);
}

/* Suggested sessions for the selected week's phase; the reasoning stays folded away. */
function PhaseQuality({ phase }: { phase: string }) {
  const q = DATA.quality[phase];
  if (!q) return null;
  return (
    <div className="wq" id="quality">
      <p className="eyebrow">Quality this phase</p>
      <ul>
        {q.sessions.map(s => (
          <li key={s.name}>
            <b>{s.name}</b> {s.detail}
          </li>
        ))}
      </ul>
      <details>
        <summary>Why &amp; sources</summary>
        <ul>
          {q.notes.map(t => (
            <li key={t}>{t}</li>
          ))}
        </ul>
        <p>
          {q.sources.map((s, i) => (
            <span key={s.url}>
              {i ? ' · ' : ''}
              <a href={s.url} target="_blank" rel="noreferrer">
                {s.label}
              </a>
            </span>
          ))}
        </p>
      </details>
    </div>
  );
}

export function PlanChart() {
  const [sel, setSel] = useState(Math.max(0, curIdx));
  // This week's Quality link shows this week's phase, whatever week was picked before.
  useEffect(() => {
    const on = () => location.hash === '#quality' && setSel(Math.max(0, curIdx));
    addEventListener('hashchange', on);
    return () => removeEventListener('hashchange', on);
  }, []);
  // Below laptop width the canvas gets larger type and stretches with the column, so a
  // phone fits the whole macrocycle and a tablet does not blow the labels up.
  const wide = useWide(),
    f = wide ? 1 : 1.55;
  const [ref, px] = useRenderedWidth<HTMLDivElement>(334);
  const W = wide ? 1140 : Math.max(620, Math.round(px / 0.54)),
    H = wide ? 380 : 420,
    m = { t: 30 * f, r: 10, b: 84 * f, l: wide ? 56 : 54 };
  const iw = W - m.l - m.r,
    ih = H - m.t - m.b;
  const top = Math.max(...P.map(p => p.run_h), ...PROV.map(q => q.run_h[1]), ...DATA.weeks.map(w => w.run_h));
  const MAXH = Math.ceil(top / 2) * 2,
    slot = iw / P.length;
  const x = (i: number) => m.l + (i + 0.5) * slot;
  const y = (v: number) => m.t + ih - (v / MAXH) * ih;
  const bw = Math.min(26, slot - (wide ? 10 : 4));
  const idx = Object.fromEntries(P.map((p, i) => [p.start, i]));
  const grid = Array.from({ length: MAXH / 2 + 1 }, (_, k) => k * 2);
  const firstProv = P.findIndex(p => !p.committed);

  const by = m.t + ih + 30 * f;
  const every = wide || (slot * px) / W >= 22;

  const ran = P.filter(p => actual[p.start] && !actual[p.start].current);
  const hit = ran.length ? ran.reduce((s, p) => s + actual[p.start].run_h / p.run_h, 0) / ran.length : 0;
  const hz = DATA.horizon;

  return (
    <section className="card plan" id="plan" aria-labelledby="plan-h">
      <div className="ch">
        <h2 id="plan-h">The {P.length}-week plan</h2>
        <p className="intro">
          Planned against actual running hours. Weeks are written only {hz.weeks} weeks ahead; later phases carry a
          band.
        </p>
      </div>
      <div className="chart" ref={ref}>
        {/* biome-ignore lint/a11y/useSemanticElements: SVG has no <fieldset>; the group exposes the week buttons. */}
        <svg
          viewBox={`0 0 ${W} ${H}`}
          role="group"
          aria-label="Planned versus actual weekly running hours across the macrocycle"
        >
          {grid.map(g => (
            <g key={g}>
              <line x1={m.l} x2={W - m.r} y1={y(g)} y2={y(g)} stroke="var(--line)" />
              <text x={m.l - 9} y={y(g) + 4} textAnchor="end" fontSize={12.5 * f} fill="var(--muted)">
                {g}h
              </text>
            </g>
          ))}
          {wide && (
            <text
              transform={`translate(14 ${m.t + ih / 2}) rotate(-90)`}
              textAnchor="middle"
              fontSize={12.5 * f}
              fill="var(--ink-2)"
            >
              Run hours
            </text>
          )}

          {PROV.map(q => {
            const a = idx[q.start];
            const last = P.reduce((acc, p, i) => (p.phase === q.phase ? i : acc), a);
            const x0 = x(a) - slot / 2 + 3,
              x1 = x(last) + slot / 2 - 3;
            const [lo, hi] = q.run_h,
              mid = (lo + hi) / 2;
            return (
              <g key={q.phase}>
                <rect
                  x={x0}
                  y={y(hi)}
                  width={x1 - x0}
                  height={y(lo) - y(hi)}
                  rx="3"
                  fill="var(--sunk-2)"
                  stroke="var(--line-2)"
                  strokeDasharray="3 3"
                />
                <line
                  x1={x0}
                  x2={x1}
                  y1={y(mid)}
                  y2={y(mid)}
                  stroke="var(--line-2)"
                  strokeWidth="1.5"
                  strokeDasharray="5 4"
                />
                {x1 - x0 > 70 * f && (
                  <text x={(x0 + x1) / 2} y={y(hi) - 7} textAnchor="middle" fontSize={11.5 * f} fill="var(--muted)">
                    {lo.toFixed(1)}–{hi.toFixed(1)} h
                  </text>
                )}
              </g>
            );
          })}

          {firstProv > 0 && (
            <g>
              <line
                x1={x(firstProv) - slot / 2}
                x2={x(firstProv) - slot / 2}
                y1={m.t - 12}
                y2={m.t + ih}
                stroke="var(--ink-2)"
                strokeDasharray="4 3"
              />
              {wide && (
                <text x={x(firstProv) - slot / 2 - 6} y={m.t + 8} textAnchor="end" fontSize={11.5} fill="var(--ink-2)">
                  written to here
                </text>
              )}
            </g>
          )}

          {P.map((p, i) => {
            if (!p.committed) return null;
            const a = actual[p.start],
              v = a ? Math.min(a.run_h, MAXH) : 0;
            return (
              <g key={p.start}>
                <rect
                  x={x(i) - bw / 2}
                  y={y(p.run_h)}
                  width={bw}
                  height={ih * (p.run_h / MAXH)}
                  rx="3"
                  fill={p.race ? 'var(--garnet-wash)' : 'var(--ghost)'}
                />
                {a && (
                  <rect
                    x={x(i) - bw / 2 + 3}
                    y={y(v)}
                    width={bw - 6}
                    height={ih * (v / MAXH)}
                    rx="2.5"
                    fill={p.race ? 'var(--garnet)' : 'var(--teal)'}
                  />
                )}
              </g>
            );
          })}

          {P.map((p, i) => {
            if (!p.race) return null;
            const band = PROV.find(q => q.phase === p.phase);
            const tip = p.committed ? Math.max(p.run_h, actual[p.start]?.run_h ?? 0) : band ? band.run_h[1] : p.run_h;
            const end = i > P.length / 2;
            return (
              <g key={p.start}>
                <line x1={x(i)} x2={x(i)} y1={m.t - 12} y2={y(tip) - 4} stroke="var(--garnet)" strokeWidth="1.5" />
                <circle cx={x(i)} cy={m.t - 12} r="3.5" fill="var(--garnet)" />
                <text
                  x={x(i) + (end ? -8 : 8)}
                  y={m.t - 8}
                  textAnchor={end ? 'end' : 'start'}
                  fontSize={11.5 * f}
                  fontWeight="600"
                  fill="var(--garnet)"
                >
                  {wide ? p.race : p.race.split(' ')[0]}
                </text>
              </g>
            );
          })}

          {sel >= 0 && <rect x={x(sel) - slot / 2} y={m.t} width={slot} height={ih} fill="var(--teal)" opacity=".13" />}
          {P.map((p, i) => (
            <g key={p.start}>
              <text
                x={x(i)}
                y={m.t + ih + 18 * f}
                textAnchor="middle"
                fontSize={12.5 * f}
                fontWeight={i === curIdx ? 700 : 400}
                fill={`var(${i === curIdx ? '--ink' : '--muted'})`}
              >
                {every || i % 2 === 0 || i === curIdx ? p.index : ''}
              </text>
              {/* biome-ignore lint/a11y/useSemanticElements: SVG has no <button>; focus selects the week. */}
              <rect
                x={x(i) - slot / 2}
                y={m.t}
                width={slot}
                height={ih + 24}
                fill="transparent"
                className="hit"
                role="button"
                tabIndex={0}
                aria-label={`W${p.index}, ${day(p.start)}${p.race ? `, ${p.race}` : ''}`}
                onPointerEnter={e => e.pointerType === 'mouse' && setSel(i)}
                onFocus={() => setSel(i)}
                onClick={() => setSel(i)}
              />
            </g>
          ))}

          {phaseSpans.map(b => {
            const x0 = x(b.a) - slot / 2 + 1,
              x1 = x(b.b) + slot / 2 - 1;
            const now = curIdx >= b.a && curIdx <= b.b;
            const name = phaseShort(b.name),
              fit = (name.length * 7.2 + 30) * f < x1 - x0;
            return (
              <g key={b.phase}>
                <rect
                  x={x0}
                  y={by}
                  width={x1 - x0}
                  height={44 * f}
                  rx="3"
                  fill={`var(${now ? '--teal-wash' : '--sunk'})`}
                  stroke={`var(${now ? '--teal-2' : '--line'})`}
                />
                <text x={(x0 + x1) / 2} y={by + 18 * f} textAnchor="middle" fontSize={12 * f} fill="var(--ink)">
                  <tspan fontWeight="600">{b.phase}</tspan>
                  {fit ? ` ${name}` : ''}
                </text>
                {(b.b - b.a + 1) * slot > 70 * f && (
                  <text x={(x0 + x1) / 2} y={by + 35 * f} textAnchor="middle" fontSize={11.5 * f} fill="var(--muted)">
                    wk {P[b.a].index}–{P[b.b].index}
                  </text>
                )}
              </g>
            );
          })}
        </svg>
      </div>
      <div className="week-detail" aria-live="polite">
        {/* The chart's week columns are ~11 px wide on a phone; these step through weeks. */}
        <div className="wd-head">
          <button type="button" aria-label="Previous week" disabled={sel === 0} onClick={() => setSel(sel - 1)}>
            ‹
          </button>
          <b>{detail(sel)[0]}</b>
          <button type="button" aria-label="Next week" disabled={sel === P.length - 1} onClick={() => setSel(sel + 1)}>
            ›
          </button>
        </div>
        {detail(sel)
          .slice(1)
          .map(l => (
            <span key={l}>{l}</span>
          ))}
        <PhaseQuality phase={P[sel].phase} />
      </div>
      <div className="legend">
        <span>
          <i className="swatch" style={{ background: 'var(--teal)' }} />
          Actual
        </span>
        <span>
          <i className="swatch" style={{ background: 'var(--ghost)' }} />
          Weekly target
        </span>
        <span>
          <i className="swatch" style={{ background: 'var(--garnet)' }} />
          Race week
        </span>
        <span>
          <i className="swatch band" />
          Phase band (not yet written)
        </span>
        {lastRace && (
          <span className="push">
            Last race: <strong>{lastRace.name}</strong> · {day(lastRace.date, true)}
          </span>
        )}
      </div>
      <p className="caption">
        Written week by week through {day(hz.date, true)}: {hz.committed} of {P.length} weeks.{' '}
        {ran.length
          ? `${ran.length} completed so far, averaging ${(hit * 100).toFixed(0)}% of planned running hours.`
          : 'Actuals appear here as weeks are completed.'}
      </p>
    </section>
  );
}
