import { useState } from 'react';
import { DATA, type Period } from './data';
import { MON, hm, n, ratio, useWide } from './format';
import { About, place } from './Week';

const months = DATA.months;
const byKey = Object.fromEntries(months.map(m => [m.label, m]));
const seasons = Object.fromEntries(DATA.seasons.map(s => [+s.label, s]));
const years = [...new Set(months.map(m => +m.label.slice(0, 4)))].reverse();
const nowKey = DATA.today.slice(0, 7);
const keyOf = (y: number, i: number) => `${y}-${String(i + 1).padStart(2, '0')}`;
// Dan's injury months, as the intro tells them; the cache records training, not injuries.
const HURT = new Set(['2024-02', '2024-03', '2025-04', '2026-01', '2026-02']);
// Mirrors tl/config.py RISK_MONTHS (Dec–Apr): six of nine overuse onsets.
const RISK = new Set([12, 1, 2, 3, 4]);

type Metric = 'h' | 't' | 'mh';
const METRIC: Record<
  Metric,
  { label: string; of: (p: Period) => number; step: (v: number) => number; ramp: string[]; unit: string }
> = {
  h: {
    label: 'Run h',
    of: p => p.run_h,
    unit: 'h',
    step: v => (v === 0 ? 0 : v < 10 ? 1 : v < 18 ? 2 : v < 26 ? 3 : v < 33 ? 4 : 5),
    ramp: ['0', '<10', '10–18', '18–26', '26–33', '33+'],
  },
  t: {
    label: 'Total h',
    of: p => p.total_h,
    unit: 'h',
    step: v => (v === 0 ? 0 : v < 20 ? 1 : v < 30 ? 2 : v < 40 ? 3 : v < 50 ? 4 : 5),
    ramp: ['0', '<20', '20–30', '30–40', '40–50', '50+'],
  },
  mh: {
    label: 'm/h',
    of: p => p.density,
    unit: 'm/h',
    step: v => (v === 0 ? 0 : v < 150 ? 1 : v < 225 ? 2 : v < 300 ? 3 : v < 375 ? 4 : 5),
    ramp: ['0', '<150', '150–225', '225–300', '300–375', '375+'],
  },
};

/* The current year compares only its completed months with the same months a year earlier;
   the month in progress would make every year look like a collapse. */
function yoy(y: number, of: (p: Period) => number): { pct: number; span: string } | null {
  const prev = seasons[y - 1],
    cur = seasons[y];
  if (!prev || !cur) return null;
  if (y !== +nowKey.slice(0, 4)) return { pct: of(cur) / of(prev) - 1, span: '' };
  const done = +nowKey.slice(5, 7) - 1;
  if (done < 1) return null;
  const sum = (yy: number) =>
    MON.slice(0, done).reduce((s, _, i) => s + (byKey[keyOf(yy, i)] ? of(byKey[keyOf(yy, i)]) : 0), 0);
  return { pct: sum(y) / sum(y - 1) - 1, span: `Jan–${MON[done - 1]}` };
}
const pctText = (p: number) => `${p > 0 ? '+' : ''}${Math.round(p * 100)}%`;

function Trend({ metric, sel, setSel }: { metric: Metric; sel: string; setSel: (k: string) => void }) {
  const wide = useWide();
  const W = wide ? 600 : 360,
    H = wide ? 128 : 140,
    m = { t: 22, r: 8, b: 18, l: wide ? 34 : 30 };
  const iw = W - m.l - m.r,
    ih = H - m.t - m.b,
    slot = iw / months.length;
  const { of, unit } = METRIC[metric];
  const vals = months.map(of);
  const top = metric !== 'mh' ? Math.ceil(Math.max(...vals, 1) / 10) * 10 : Math.ceil(Math.max(...vals, 1) / 100) * 100;
  const x = (i: number) => m.l + (i + 0.5) * slot;
  const y = (v: number) => m.t + ih - (v / top) * ih;
  // The month in progress is a hollow dot outside the line and the average.
  const done = months.filter(p => p.label !== nowKey).length;
  const line = (vs: number[]) => vs.map((v, i) => `${i ? 'L' : 'M'}${x(i).toFixed(1)},${y(v).toFixed(1)}`).join('');
  const full = vals.slice(0, done);
  const avg = full.map((_, i) => (i < 2 ? null : (full[i] + full[i - 1] + full[i - 2]) / 3));
  const avgPath = avg
    .map((v, i) => (v === null ? '' : `${avg[i - 1] == null ? 'M' : 'L'}${x(i).toFixed(1)},${y(v).toFixed(1)}`))
    .join('');
  const bands: [number, number][] = [];
  months.forEach((p, i) => {
    if (!HURT.has(p.label)) return;
    const b = bands[bands.length - 1];
    if (b && b[1] === i - 1) b[1] = i;
    else bands.push([i, i]);
  });
  const si = months.findIndex(p => p.label === sel);
  const grid = metric !== 'mh' ? [0, top / 2, top] : [0, 300, top];
  return (
    <svg
      className="trend"
      viewBox={`0 0 ${W} ${H}`}
      role="img"
      aria-label={`Monthly ${{ h: 'running hours', t: 'total training hours', mh: 'climb per running hour' }[metric]} since ${months[0].label}, with a three-month average and injury periods`}
    >
      {bands.map(([a, b]) => (
        <g key={a}>
          <rect x={x(a) - slot / 2} y={m.t} width={(b - a + 1) * slot} height={ih} fill="var(--garnet-wash)" />
          <text x={x(a) - slot / 2 + 2} y={m.t + 9} fontSize="8.5" fill="var(--garnet)">
            injury
          </text>
        </g>
      ))}
      {grid.map(g => (
        <g key={g}>
          <line
            x1={m.l}
            x2={W - m.r}
            y1={y(g)}
            y2={y(g)}
            stroke={metric === 'mh' && g === 300 ? 'var(--garnet)' : 'var(--line)'}
            strokeDasharray={metric === 'mh' && g === 300 ? '3 3' : undefined}
          />
          <text x={m.l - 5} y={y(g) + 3} textAnchor="end" fontSize="9" fill="var(--muted)">
            {g}
            {g === top && metric !== 'mh' ? 'h' : ''}
          </text>
        </g>
      ))}
      {months.map(
        (p, i) =>
          p.label.endsWith('-01') && (
            <text key={p.label} x={x(i) - slot / 2} y={H - 5} fontSize="9" fill="var(--muted)">
              {p.label.slice(0, 4)}
            </text>
          ),
      )}
      {done > 0 && (
        <>
          <path d={`${line(full)}L${x(done - 1)},${y(0)}L${x(0)},${y(0)}Z`} fill="var(--teal-wash)" />
          <path d={line(full)} fill="none" stroke="var(--teal)" strokeWidth="1.6" strokeLinejoin="round" />
        </>
      )}
      {avgPath && <path d={avgPath} fill="none" stroke="var(--ink-2)" strokeWidth="1" strokeDasharray="3 2.5" />}
      {done < months.length && (
        <circle cx={x(done)} cy={y(vals[done])} r="2.5" fill="var(--surface)" stroke="var(--teal)" />
      )}
      {si >= 0 && (
        <>
          <line x1={x(si)} x2={x(si)} y1={m.t} y2={m.t + ih} stroke="var(--ink)" strokeWidth="1" opacity=".5" />
          <circle cx={x(si)} cy={y(vals[si])} r="3.2" fill="var(--ink)" />
          <text
            x={Math.min(Math.max(x(si), m.l + 16), W - m.r - 16)}
            y={m.t - 7}
            textAnchor="middle"
            fontSize="9"
            fill="var(--ink)"
          >
            {metric !== 'mh' ? vals[si].toFixed(1) : vals[si]} {unit}
          </text>
        </>
      )}
      {months.map((p, i) => (
        <rect
          key={p.label}
          className="hit"
          x={x(i) - slot / 2}
          y={m.t}
          width={slot}
          height={ih + m.b}
          fill="transparent"
          onPointerEnter={e => e.pointerType === 'mouse' && setSel(p.label)}
          onClick={() => setSel(p.label)}
        />
      ))}
    </svg>
  );
}

function Split({ p }: { p: Period }) {
  const other = Math.max(0, p.total_h - p.run_h - p.bike_h - p.gym_h);
  const parts = (
    [
      ['run', p.run_h],
      ['bike', p.bike_h],
      ['gym', p.gym_h],
      ['other', other],
    ] as const
  ).filter(([, v]) => v >= 0.05);
  return (
    <div className="split">
      <div className="split-bar">
        {parts.map(([k, v]) => (
          <i key={k} className={k} style={{ flexGrow: v }} title={`${k} ${v.toFixed(1)} h`} />
        ))}
      </div>
      <span>
        {[...parts.map(([k, v]) => `${k} ${v.toFixed(1)}\u00a0h`), `total ${p.total_h.toFixed(1)}\u00a0h`].join(' · ')}
      </span>
    </div>
  );
}

function SameMonth({ sel, metric }: { sel: string; metric: Metric }) {
  const mon = +sel.slice(5, 7) - 1,
    { of, unit } = METRIC[metric];
  const rows = [...years]
    .reverse()
    .map(y => ({ y, key: keyOf(y, mon), p: byKey[keyOf(y, mon)] }))
    .filter(r => r.p);
  const top = Math.max(...rows.map(r => of(r.p)), 1);
  return (
    <div className="same">
      <span className="eyebrow">{MON[mon]} each year</span>
      <ul>
        {rows.map(r => (
          <li key={r.y} className={r.key === sel ? 'on' : ''}>
            <i style={{ height: `${(of(r.p) / top) * 100}%` }} />
            <b>
              {metric !== 'mh' ? of(r.p).toFixed(0) : of(r.p)}
              {r.key === nowKey ? '*' : ''}
            </b>
            <small>{r.y}</small>
          </li>
        ))}
      </ul>
      <small className="unit">
        {unit}
        {rows.some(r => r.key === nowKey) ? ' · * to date' : ''}
      </small>
    </div>
  );
}

export function Heatmap() {
  const [sel, setSel] = useState(nowKey);
  const [metric, setMetric] = useState<Metric>('h');
  const M = METRIC[metric];
  const m = byKey[sel];
  const i = months.findIndex(p => p.label === sel);
  const prev = i > 0 ? months[i - 1] : null;
  const ramp = m && prev && prev.run_h > 0 && sel !== nowKey ? m.run_h / prev.run_h : null;
  const sy = +sel.slice(0, 4),
    yc = yoy(sy, metric === 't' ? M.of : METRIC.h.of);
  return (
    <section className="card heat" aria-labelledby="map-h">
      <div className="ch">
        <h2 id="map-h">Every month since {years[years.length - 1]}</h2>
        <div className="mode push" role="group" aria-label="Metric">
          {(['h', 't', 'mh'] as const).map(k => (
            <button
              key={k}
              aria-pressed={metric === k}
              className={metric === k ? 'on' : ''}
              onClick={() => setMetric(k)}
            >
              {METRIC[k].label}
            </button>
          ))}
        </div>
      </div>
      <p className="intro">
        The gaps are the injuries: February–March 2024, April 2025, and the two months the January 2026 calf cost.
        {metric === 'mh' &&
          ` Climb per running hour: below ${DATA.guardrails.vert_floor} m/h is the flat volume behind the calf and shin failures.`}{' '}
        Hover or tap a month.
      </p>
      <Trend metric={metric} sel={sel} setSel={setSel} />
      <div className="mapgrid">
        <span />
        {MON.map((x, k) => (
          <span key={x} className={`hd${RISK.has(k + 1) ? ' risk' : ''}`}>
            {x}
          </span>
        ))}
        <span className="hd">Year</span>
        {years.map(y => {
          const s = seasons[y],
            d = yoy(y, M.of);
          return [
            <span key={y} className="yr">
              {y}
            </span>,
            ...MON.map((_, k) => {
              const key = keyOf(y, k),
                mm = byKey[key],
                s2 = M.step(mm ? M.of(mm) : 0);
              return (
                <button
                  key={key}
                  className={`cell${key === nowKey ? ' now' : ''}${key === sel ? ' sel' : ''}${HURT.has(key) ? ' hurt' : ''}`}
                  style={{ backgroundColor: `var(--s${s2})`, color: `var(--on-s${s2})` }}
                  aria-label={`${key}${HURT.has(key) ? ', injury' : ''}${key === nowKey ? ', to date' : ''}`}
                  onPointerEnter={e => e.pointerType === 'mouse' && setSel(key)}
                  onClick={() => setSel(key)}
                >
                  {mm &&
                    (metric !== 'mh' ? (
                      <>
                        <b>{M.of(mm).toFixed(0)}</b>
                        <i>{metric === 'h' ? `${Math.round(mm.run_km)} km` : `${mm.run_h.toFixed(0)} run`}</i>
                      </>
                    ) : (
                      <>
                        <b>{mm.density}</b>
                        <i>{(mm.run_vert / 1000).toFixed(1)}k</i>
                      </>
                    ))}
                </button>
              );
            }),
            <span
              key={`${y}-t`}
              className="ytot"
              title={d?.span ? `${y} to date; change compares ${d.span}` : undefined}
            >
              {s &&
                (metric !== 'mh' ? (
                  <>
                    <b>{M.of(s).toFixed(0)}</b>
                    {d && <i className={d.pct < 0 ? 'dn' : ''}>{pctText(d.pct)}</i>}
                  </>
                ) : (
                  <>
                    <b>{s.density}</b>
                    <i>m/h</i>
                  </>
                ))}
            </span>,
          ];
        })}
      </div>
      <div className="ramp">
        {M.ramp.map((l, k) => (
          <span key={l}>
            <i style={{ background: `var(--s${k})` }} />
            {l} {M.unit}
          </span>
        ))}
        <span>
          <i className="hurt-key" />
          injury
        </span>
        <span>
          <i className="risk-key" />
          Dec–Apr risk months
        </span>
        <span>
          · garnet outline: this month, to date{metric === 't' && ' · small: run hours'}
          {metric === 'mh' && ' · small: thousand metres climbed'}
        </span>
      </div>
      <div className="week-detail month-detail" aria-live="polite">
        <b>
          {sel}
          {HURT.has(sel) && <em className="tag">injury</em>}
          {RISK.has(+sel.slice(5, 7)) && <em className="tag">Dec–Apr</em>}
          {sel === nowKey && <em className="tag">to date</em>}
        </b>
        {m ? (
          <>
            <div className="md-text">
              <span>
                {m.run_h.toFixed(1)} h run · {m.run_km.toFixed(0)} km · {n(m.run_vert)} m · {m.density} m/h
              </span>
              {ramp !== null && prev && (
                <span className={ramp > DATA.guardrails.wow ? 'up' : ''}>
                  {ratio(ramp)}× {MON[+prev.label.slice(5, 7) - 1]}'s running hours
                </span>
              )}
              <span>
                {m.run_days} run days · longest {hm(m.longest / 60)} · {m.quality} quality · feel{' '}
                {m.feel === null ? '—' : `${m.feel > 0 ? '+' : ''}${m.feel.toFixed(1)}`}
              </span>
              {m.hr !== null && m.pace !== null && (
                <span>
                  easy/long HR {m.hr.toFixed(0)} bpm at {hm(m.pace)} /km
                </span>
              )}
              {seasons[sy] && (
                <span>
                  {sy}
                  {yc?.span ? ' to date' : ''}: {seasons[sy].run_h.toFixed(0)} h run · {seasons[sy].total_h.toFixed(0)}{' '}
                  h total
                  {yc &&
                    ` · ${pctText(yc.pct)} ${metric === 't' ? 'total' : 'run'} vs ${sy - 1}${yc.span ? ` (${yc.span})` : ''}`}
                </span>
              )}
              <Split p={m} />
            </div>
            <SameMonth sel={sel} metric={metric} />
          </>
        ) : (
          <span>nothing recorded</span>
        )}
      </div>
    </section>
  );
}

/* The table scrolls, so its cards are popovers in the top layer: a mouse opens one on
   hover and a tap toggles it. Cancelling a mouse click keeps the hovered card open. */
function FlagChip({ code, id }: { code: string; id: string }) {
  const mouse = (e: React.PointerEvent) => e.pointerType === 'mouse';
  return (
    <>
      <button
        type="button"
        className="chip bad"
        popoverTarget={id}
        onPointerEnter={e => {
          if (!mouse(e)) return;
          document.getElementById(id)?.showPopover();
          place(e, id);
        }}
        onPointerLeave={e => mouse(e) && document.getElementById(id)?.hidePopover()}
        onClick={e =>
          'pointerType' in e.nativeEvent && e.nativeEvent.pointerType === 'mouse' ? e.preventDefault() : place(e, id)
        }
      >
        {code}
      </button>
      <span id={id} popover="auto" className="tip about">
        <About code={code} />
      </span>
    </>
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
      <p className="intro">
        Every week scored against the guardrails. WoW and ACWR are running hours only — the bike carries load the
        tendons never see.
      </p>
      <div className="tw">
        <table>
          <thead>
            <tr>
              <th>Week</th>
              <th className="n">Run h</th>
              <th className="n">Plan</th>
              <th className="n">km</th>
              <th className="n">Vert</th>
              <th className="n">m/h</th>
              <th className="n">Bike</th>
              <th className="n">Gym</th>
              <th className="n">Total</th>
              <th className="n">WoW</th>
              <th className="n">ACWR</th>
              <th>Rails</th>
            </tr>
          </thead>
          <tbody>
            {rows.map(w => {
              const p = planBy[w.start];
              return (
                <tr key={w.start} className={w.current ? 'now' : w.flags.length ? 'flagged' : ''}>
                  <td className="mono" title={`Monday ${w.start}`}>
                    {w.label}
                  </td>
                  <td className="n">{w.run_h.toFixed(1)}</td>
                  <td className="n">{p ? p.run_h.toFixed(1) : '—'}</td>
                  <td className="n">{w.km.toFixed(0)}</td>
                  <td className="n">{n(w.vert)}</td>
                  <td className="n">{w.density}</td>
                  <td className="n">{w.bike_h.toFixed(1)}</td>
                  <td className="n">{w.gym_h.toFixed(1)}</td>
                  <td className="n">{w.total_h.toFixed(1)}</td>
                  <td className="n">{ratio(w.wow)}</td>
                  <td className="n">{ratio(w.acwr)}</td>
                  <td>
                    {w.flags.length ? (
                      w.flags.map(f => <FlagChip key={f} code={f} id={`flag-${w.start}-${f}`} />)
                    ) : (
                      <span className="chip ok">ok</span>
                    )}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
      <p className="note">
        <b>Flags.</b> <span className="chip bad">R1</span> WoW jump above {DATA.guardrails.wow}×, the strongest injury
        predictor in the record. <span className="chip bad">R2</span> ACWR above {DATA.guardrails.acwr.toFixed(2)}.{' '}
        <span className="chip bad">R3</span> over {DATA.guardrails.big_week_h} h below {DATA.guardrails.vert_floor} m/h
        — flat volume. <span className="chip bad">R6</span> over {DATA.guardrails.km} km. R4 fires only for{' '}
        <em>flat</em> I/R work.
      </p>
    </section>
  );
}
