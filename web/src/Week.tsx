import { DATA, type Fit } from './data';
import { MON, current as w, day, n, phaseShort, rails, signed, span, type Rail } from './format';

const MARK = { ok: '✓', watch: '!', bad: '✕' };

export function ThisWeek({ children }: { children?: React.ReactNode }) {
  if (!w) return null;
  const p = w.plan,
    G = DATA.guardrails;
  const r = p?.run_h ? w.run_h / p.run_h : null;
  const R = 74,
    C = 2 * Math.PI * R;
  const stats: [string, string, string, string][] = [
    [String(Math.round(w.run_km)), 'km', p ? `of ${Math.round(p.run_km)} planned` : 'this week', ''],
    [n(w.run_vert), 'm vert', p ? `of ${n(p.run_vert)} planned` : 'this week', ''],
    [String(w.density), 'm/h density', `floor ${G.vert_floor} m/h`, w.density < G.vert_floor ? 'warn' : ''],
    [p ? p.weekend : '—', 'weekend', 'planned', 'txt'],
  ];
  return (
    <section className="card now" aria-labelledby="now-h">
      <div className="ch">
        <h2 id="now-h">This week</h2>
        <span className="meta">
          {p ? `Week ${p.index} of ${DATA.plan.length} · ` : ''}
          {span(w.start, w.end)}
        </span>
        <span className="pill">
          {p ? (
            <>
              <b>{p.phase}</b>
              {phaseShort(p.phase_name)}
            </>
          ) : (
            'Lead-in'
          )}
        </span>
      </div>
      <div className="tw-main">
        <div className="ring">
          <svg viewBox="0 0 172 172" aria-hidden="true">
            <circle cx="86" cy="86" r={R} fill="none" stroke="var(--sunk-2)" strokeWidth="15" />
            <circle
              cx="86"
              cy="86"
              r={R}
              fill="none"
              stroke={r !== null && r > 1.15 ? 'var(--amber)' : 'var(--teal)'}
              strokeWidth="15"
              strokeLinecap="round"
              strokeDasharray={`${C * Math.min(1, r ?? 0)} ${C}`}
            />
          </svg>
          <div className="c">
            <b>
              {w.run_h.toFixed(1)}
              {p ? ` / ${p.run_h.toFixed(1)}` : ''} h
            </b>
            {r !== null && <i>{Math.round(r * 100)}%</i>}
            <span>run hours</span>
          </div>
        </div>
        <div className="stats">
          {stats.map(([v, u, s, cls]) => (
            <div key={u}>
              <b className={cls}>{v}</b>
              <span>{u}</span>
              <small>{s}</small>
            </div>
          ))}
        </div>
      </div>
      {children}
    </section>
  );
}

function Dots({ rail }: { rail: Rail }) {
  return (
    // The empty title stops the row's native tooltip from covering the hover card.
    <span
      className="dots"
      title=""
      aria-label={`last ${rail.history.length} weeks: ${rail.history.map(h => `${h.week} ${h.value}`).join(', ')}`}
    >
      {rail.history.map(h => (
        <i key={h.week} className={h.status}>
          <span className="tip" aria-hidden="true">
            <small>
              {h.week}
              {h.current ? ' · this week' : ''}
            </small>
            <em>{h.dates}</em>
            <b>{h.value}</b>
            <span>{h.note}</span>
          </span>
        </i>
      ))}
    </span>
  );
}

export function Guardrails() {
  const list = rails();
  return (
    <section className="card rails" aria-labelledby="rails-h">
      <div className="ch">
        <h2 id="rails-h">Training guardrails</h2>
        <span className="meta push">6-week trend</span>
      </div>
      <ul className="rail-list">
        {list.map(r => (
          <li key={r.code} className={r.status} title={r.why}>
            <i className="mark">{MARK[r.status]}</i>
            <div>
              <b>{r.value}</b>
              <span>
                {r.code} · {r.rule}
              </span>
            </div>
            <Dots rail={r} />
          </li>
        ))}
      </ul>
    </section>
  );
}

/* Phone: one swipeable row of chips inside the this-week card. */
export function RailChips() {
  const list = rails();
  const ok = list.filter(r => r.status === 'ok').length;
  return (
    <div className="chips-wrap">
      <div className="ch">
        <p className="eyebrow">Training guardrails</p>
        <span className="meta push">
          {ok} of {list.length} in range
        </span>
      </div>
      <div className="chips" role="list">
        {list.map(r => (
          <div key={r.code} role="listitem" className={`rchip ${r.status}`} title={r.why}>
            <i className="mark">{MARK[r.status]}</i>
            <div>
              <b>{r.value}</b>
              <span>
                {r.code} · {r.rule}
              </span>
            </div>
            <Dots rail={r} />
          </div>
        ))}
      </div>
    </div>
  );
}

function FitChart({ F, H }: { F: Fit[]; H: number }) {
  const W = 380,
    m = { t: 8, r: 6, b: 22, l: 30 };
  const lo = Math.floor(Math.min(0, ...F.map(d => d.tsb)) / 10) * 10;
  const hi = Math.ceil(Math.max(...F.map(d => Math.max(d.ctl, d.atl))) / 10) * 10;
  const x = (i: number) => m.l + (i / (F.length - 1)) * (W - m.l - m.r);
  const y = (v: number) => m.t + ((hi - v) / (hi - lo)) * (H - m.t - m.b);
  const step = hi - lo > 60 ? 20 : 10;
  const grid = [];
  for (let g = lo; g <= hi; g += step) grid.push(g);
  const line = (k: 'ctl' | 'atl' | 'tsb') => F.map((d, i) => `${x(i).toFixed(1)},${y(d[k]).toFixed(1)}`).join(' ');
  return (
    <svg viewBox={`0 0 ${W} ${H}`} role="img" aria-label="Daily fitness, fatigue and form over the last 12 weeks">
      {grid.map(g => (
        <g key={g}>
          <line x1={m.l} x2={W - m.r} y1={y(g)} y2={y(g)} stroke={`var(${g === 0 ? '--line-2' : '--line'})`} />
          <text x={m.l - 6} y={y(g) + 4} textAnchor="end" fontSize="11" fill="var(--muted)">
            {g}
          </text>
        </g>
      ))}
      {F.map(
        (d, i) =>
          d.date.endsWith('-01') && (
            <text
              key={d.date}
              x={x(i)}
              y={H - 5}
              textAnchor={i > F.length - 6 ? 'end' : 'middle'}
              fontSize="11"
              fill="var(--muted)"
            >
              {MON[+d.date.slice(5, 7) - 1]}
            </text>
          ),
      )}
      <polyline fill="none" stroke="var(--line-2)" strokeWidth="1.6" strokeLinejoin="round" points={line('atl')} />
      <polyline fill="none" stroke="var(--garnet)" strokeWidth="1.8" strokeLinejoin="round" points={line('tsb')} />
      <polyline fill="none" stroke="var(--teal)" strokeWidth="2.4" strokeLinejoin="round" points={line('ctl')} />
    </svg>
  );
}

export function Fitness({ compact = false }: { compact?: boolean }) {
  const F = DATA.fitness,
    f = F[F.length - 1];
  if (!f) return null;
  return (
    <section className="card fit" aria-labelledby="fit-h">
      <div className="ch">
        <h2 id="fit-h">{compact ? 'Fitness trend' : 'Fitness & form'}</h2>
        <span className="meta push">
          {day(F[0].date)} – {day(f.date)}
        </span>
      </div>
      <dl className="fit-nums">
        <div>
          <dt>CTL</dt>
          <dd>{f.ctl.toFixed(0)}</dd>
          <small>chronic load</small>
        </div>
        <div>
          <dt>ATL</dt>
          <dd>{f.atl.toFixed(0)}</dd>
          <small>acute load</small>
        </div>
        <div>
          <dt>Form</dt>
          <dd className={f.tsb >= 0 ? 'pos' : 'neg'}>{signed(f.tsb)}</dd>
          <small>into today</small>
        </div>
      </dl>
      <div className="legend">
        <span>
          <i className="swatch round" style={{ background: 'var(--teal)' }} />
          CTL
        </span>
        <span>
          <i className="swatch round" style={{ background: 'var(--line-2)' }} />
          ATL
        </span>
        <span>
          <i className="swatch round" style={{ background: 'var(--garnet)' }} />
          Form
        </span>
      </div>
      <FitChart F={F} H={compact ? 140 : 190} />
      {!compact && (
        <p className="caption">
          Daily load units from the HR model. The shape carries the information; the absolute numbers depend on the load
          model.
        </p>
      )}
    </section>
  );
}
