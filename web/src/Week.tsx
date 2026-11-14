import { type ReactNode, useState } from 'react';
import { DATA, type Fit } from './data';
import {
  GUARDRAIL,
  MARK,
  MON,
  addDays,
  current as w,
  curIdx,
  day,
  isoWeek,
  n,
  phaseShort,
  planWeek,
  rails,
  signed,
  span,
  useRenderedWidth,
  type Rail,
  type RailWeek,
  type Status,
} from './format';

// A link to the hash already in the URL fires no hashchange; fire one so the plan
// returns to this week and the page scrolls.
const sameHash = (e: React.MouseEvent<HTMLAnchorElement>) => {
  if (location.hash !== e.currentTarget.hash) return;
  e.preventDefault();
  dispatchEvent(new HashChangeEvent('hashchange'));
};

export function ThisWeek({ children }: { children?: ReactNode }) {
  if (!w) return null;
  const p = w.plan,
    G = DATA.guardrails;
  const q = p && DATA.quality[p.phase];
  const r = p?.run_h ? w.run_h / p.run_h : null;
  const r3 = rails().find(x => x.code === 'R3')?.status ?? 'ok';
  const next = curIdx >= 0 ? DATA.plan[curIdx + 1] : undefined;
  const R = 74,
    C = 2 * Math.PI * R;
  const stats: [string, string, string, Status][] = [
    [String(Math.round(w.run_km)), 'km', p ? `of ${Math.round(p.run_km)} planned` : 'this week', 'ok'],
    [
      n(w.run_vert),
      'm vert',
      p ? (p.run_vert === null ? 'no target' : `of ${n(p.run_vert)} planned`) : 'this week',
      'ok',
    ],
    [String(w.density), 'm/h', `climb density · floor ${G.vert_floor}`, r3],
  ];
  return (
    <section className="card now" id="today" aria-labelledby="now-h">
      <div className="ch">
        <h2 id="now-h">This week</h2>
        <span className="meta" title={isoWeek(w.start)}>
          {[planWeek(w.start), span(w.start, w.end)].filter(Boolean).join(' · ')}
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
            <b>{w.run_h.toFixed(1)} h</b>
            {p && r !== null && (
              <i>
                of {p.run_h.toFixed(1)} · {Math.round(r * 100)}%
              </i>
            )}
            <span>run hours</span>
          </div>
        </div>
        <div className="stats">
          {stats.map(([v, u, s, st]) => (
            <div key={u}>
              <b className={st}>{v}</b>
              <span>{u}</span>
              <small>{s}</small>
            </div>
          ))}
        </div>
      </div>
      {children}
      <dl className="tw-lines">
        {p && (
          <div>
            <dt className="eyebrow">Weekend</dt>
            <dd>{p.weekend}</dd>
          </div>
        )}
        {q && (
          <div>
            <dt className="eyebrow">Quality</dt>
            <dd>
              {/* biome-ignore lint/a11y/useValidAnchor: it navigates to #quality; the handler only re-fires a repeated hash. */}
              <a href="#quality" onClick={sameHash}>
                {q.sessions.map(s => s.name).join(' · ')}
                <i aria-hidden="true"> ›</i>
              </a>
            </dd>
          </div>
        )}
        {/* The plan's own numbers for next week, nothing derived: Dan plans, the page checks. */}
        {next?.committed && (
          <div>
            <dt className="eyebrow">Next</dt>
            <dd>
              W{next.index} · {span(next.start, addDays(next.start, 6))} · plan {next.run_h.toFixed(1)} h run ·{' '}
              {Math.round(next.km)} km{next.race ? ` · ${next.race}` : ` · ${next.weekend}`}
            </dd>
          </div>
        )}
      </dl>
    </section>
  );
}

function TipBody({ h }: { h: RailWeek }) {
  return (
    <>
      <small>
        {h.week}
        {h.current ? ' · this week' : ''}
      </small>
      <em>{h.dates}</em>
      <b>{h.value}</b>
      <span>
        <i className={`mark sm ${h.status}`} aria-hidden="true">
          {MARK[h.status]}
        </i>{' '}
        {h.status} · {h.note}
      </span>
    </>
  );
}

export function About({ code }: { code: string }) {
  const [name, about] = GUARDRAIL[code];
  return (
    <>
      <small>{code} · guardrail</small>
      <strong>{name}</strong>
      <span>{about}</span>
    </>
  );
}

/* The card goes above its trigger, or below it near the top of the screen, clamped to the
   viewport. It is measured after the popover opens, in the frame before it paints. */
export function place(e: React.MouseEvent<HTMLButtonElement>, id: string) {
  const d = e.currentTarget.getBoundingClientRect();
  requestAnimationFrame(() => {
    const p = document.getElementById(id);
    if (!p?.matches(':popover-open')) return;
    const cx = d.left + d.width / 2;
    const left = Math.min(Math.max(8, cx - p.offsetWidth / 2), innerWidth - p.offsetWidth - 8);
    const below = d.top - p.offsetHeight - 12 < 8;
    p.style.left = `${left}px`;
    p.style.top = `${below ? d.bottom + 12 : d.top - p.offsetHeight - 12}px`;
    p.style.setProperty('--ax', `${cx - left}px`);
    p.classList.toggle('below', below);
  });
}

/* Each dot is a button. With a mouse its card shows on hover or keyboard focus; on a
   touch screen a tap opens it as a popover, in the top layer so nothing clips it. */
function Dots({ rail, tap }: { rail: Rail; tap: boolean }) {
  const id = (i: number) => `tip-${rail.code}-${i}`;
  const label = (h: RailWeek) => `${rail.code} ${h.week}${h.current ? ', this week' : ''}: ${h.value}, ${h.status}`;
  if (tap)
    return (
      <>
        <span className="dots">
          {rail.history.map((h, i) => (
            <button
              key={h.week}
              type="button"
              className={h.status}
              aria-label={label(h)}
              popoverTarget={id(i)}
              onClick={e => place(e, id(i))}
            />
          ))}
        </span>
        {rail.history.map((h, i) => (
          <span key={h.week} id={id(i)} popover="auto" className={`tip ${h.status}`}>
            <TipBody h={h} />
          </span>
        ))}
      </>
    );
  return (
    <span className="dots">
      {rail.history.map((h, i) => (
        <button key={h.week} type="button" className={h.status} aria-label={label(h)} aria-describedby={id(i)}>
          <span id={id(i)} className={`tip ${h.status}`} aria-hidden="true">
            <TipBody h={h} />
          </span>
        </button>
      ))}
    </span>
  );
}

function railSummary(list: Rail[]) {
  const off = (s: Status) => list.filter(r => r.status === s).map(r => r.code);
  return [
    // A watch is not a breach, so it counts as within limits and is named after.
    `${list.length - off('flag').length} of ${list.length} within limits`,
    off('flag').length ? `flag ${off('flag').join(', ')}` : '',
    off('watch').length ? `watch ${off('watch').join(', ')}` : '',
  ]
    .filter(Boolean)
    .join(' · ');
}

/* The same list on the laptop card and inside the phone's this-week card: the rule's name
   first, then this week's value against its limit, then six weeks of dots. A watch or flag
   says why on its own line. */
function RailRows({ tap }: { tap: boolean }) {
  const SEVERITY = { flag: 0, watch: 1, ok: 2 };
  const list = rails().sort((a, b) => SEVERITY[a.status] - SEVERITY[b.status]);
  return (
    <ul className="rail-list">
      {list.map(r => (
        <li key={r.code} className={r.status}>
          <i className={`mark ${r.status}`} role="img" aria-label={r.status}>
            {MARK[r.status]}
          </i>
          {tap ? (
            <>
              <button
                type="button"
                className="rule"
                popoverTarget={`about-${r.code}`}
                onClick={e => place(e, `about-${r.code}`)}
              >
                <RuleText r={r} />
              </button>
              <span id={`about-${r.code}`} popover="auto" className="tip about">
                <About code={r.code} />
              </span>
            </>
          ) : (
            <button type="button" className="rule" aria-describedby={`about-${r.code}`}>
              <RuleText r={r} />
              <span id={`about-${r.code}`} className="tip about" aria-hidden="true">
                <About code={r.code} />
              </span>
            </button>
          )}
          <Dots rail={r} tap={tap} />
          {r.note && <p className="rnote">{r.note}</p>}
        </li>
      ))}
    </ul>
  );
}

function RuleText({ r }: { r: Rail }) {
  return (
    <>
      <span className="rn">
        {r.name} <small>{r.code}</small>
      </span>
      <span className="rv">
        <b>{r.value}</b> <span>{r.rule}</span>
      </span>
    </>
  );
}

export function Guardrails({ inline = false }: { inline?: boolean }) {
  const list = rails();
  const head = (
    <div className="ch">
      <h2 id="rails-h">Training guardrails</h2>
      <span className="meta push">{railSummary(list)}</span>
    </div>
  );
  if (inline)
    return (
      <section className="rails-inline" id="rails" aria-labelledby="rails-h">
        {head}
        <RailRows tap />
      </section>
    );
  return (
    <section className="card rails" id="rails" aria-labelledby="rails-h">
      {head}
      <RailRows tap={false} />
      <p className="caption">Dots: the last six weeks, this week ringed. Hover a dot or a rule for details.</p>
    </section>
  );
}

function FitChart({ F, tall }: { F: Fit[]; tall: number }) {
  const W = 380;
  const [ref, px] = useRenderedWidth<SVGSVGElement>(W);
  // The height stays put on screen as the column widens; the time axis stretches instead.
  const H = (tall * W) / px;
  // 11 px on screen, whatever the column width.
  const fs = (11 * W) / px;
  const m = { t: 6 + 1.4 * fs, r: 6, b: 8 + 1.4 * fs, l: 2.8 * fs };
  const lo = Math.floor(Math.min(0, ...F.map(d => d.tsb)) / 10) * 10;
  const hi = Math.ceil(Math.max(...F.map(d => Math.max(d.ctl, d.atl))) / 10) * 10;
  const x = (i: number) => m.l + (i / (F.length - 1)) * (W - m.l - m.r);
  const y = (v: number) => m.t + ((hi - v) / (hi - lo)) * (H - m.t - m.b);
  const step = hi - lo > 60 ? 20 : 10;
  // Gridlines step from zero, so the zero line Form crosses is always drawn.
  const grid = [];
  for (let g = Math.ceil(lo / step) * step; g <= hi; g += step) grid.push(g);
  const line = (k: 'ctl' | 'atl' | 'tsb') => F.map((d, i) => `${x(i).toFixed(1)},${y(d[k]).toFixed(1)}`).join(' ');
  // Hover or tap reads out the nearest day; the numbers above show the latest.
  const [at, setAt] = useState<number | null>(null);
  const pick = (e: React.PointerEvent<SVGSVGElement>) => {
    const r = e.currentTarget.getBoundingClientRect();
    const u = ((e.clientX - r.left) / r.width) * W;
    setAt(Math.max(0, Math.min(F.length - 1, Math.round(((u - m.l) / (W - m.l - m.r)) * (F.length - 1)))));
  };
  const d = at === null ? null : F[at];
  return (
    <svg
      ref={ref}
      viewBox={`0 0 ${W} ${H}`}
      role="img"
      aria-label="Daily fitness, fatigue and form over the last 12 weeks"
      onPointerMove={pick}
      onPointerDown={pick}
      onPointerLeave={e => e.pointerType === 'mouse' && setAt(null)}
    >
      {grid.map(g => (
        <g key={g}>
          <line
            x1={m.l}
            x2={W - m.r}
            y1={y(g)}
            y2={y(g)}
            stroke={`var(${g === 0 ? '--ink-2' : '--line'})`}
            strokeWidth={g === 0 ? 1 : 0.8}
          />
          <text x={m.l - 5} y={y(g) + fs / 3} textAnchor="end" fontSize={fs} fill="var(--muted)">
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
              y={H - 4}
              textAnchor={i > F.length - 6 ? 'end' : 'middle'}
              fontSize={fs}
              fill="var(--muted)"
            >
              {MON[+d.date.slice(5, 7) - 1]}
            </text>
          ),
      )}
      <polyline fill="none" stroke="var(--slate)" strokeWidth="1.5" strokeLinejoin="round" points={line('atl')} />
      <polyline
        fill="none"
        stroke="var(--ink-2)"
        strokeWidth="1.5"
        strokeDasharray="4 2.5"
        strokeLinejoin="round"
        points={line('tsb')}
      />
      <polyline fill="none" stroke="var(--teal)" strokeWidth="2.4" strokeLinejoin="round" points={line('ctl')} />
      {d && at !== null && (
        <g>
          <line x1={x(at)} x2={x(at)} y1={m.t} y2={H - m.b} stroke="var(--ink)" strokeWidth="0.8" opacity=".5" />
          <circle cx={x(at)} cy={y(d.ctl)} r={fs / 3.5} fill="var(--teal)" />
          <text
            x={Math.min(Math.max(x(at), m.l + 9 * fs), W - m.r - 9 * fs)}
            y={m.t - fs / 2}
            textAnchor="middle"
            fontSize={fs}
            fill="var(--ink)"
            stroke="var(--surface)"
            strokeWidth={fs / 3}
            paintOrder="stroke"
          >
            {day(d.date)} · CTL {d.ctl.toFixed(0)} · ATL {d.atl.toFixed(0)} · form {signed(d.tsb)}
          </text>
        </g>
      )}
    </svg>
  );
}

export function Fitness({ compact = false }: { compact?: boolean }) {
  const F = DATA.fitness,
    f = F[F.length - 1];
  if (!f) return null;
  return (
    <section className="card fit" id="fitness" aria-labelledby="fit-h">
      <div className="ch">
        <h2 id="fit-h">Fitness &amp; form</h2>
        <span className="meta push">
          {day(F[0].date)} – {day(f.date)}
        </span>
      </div>
      <dl className="fit-nums">
        <div>
          <dt>
            <i className="swatch line" style={{ background: 'var(--teal)' }} />
            CTL
          </dt>
          <dd>{f.ctl.toFixed(0)}</dd>
          <small>fitness</small>
        </div>
        <div>
          <dt>
            <i className="swatch line" style={{ background: 'var(--slate)' }} />
            ATL
          </dt>
          <dd>{f.atl.toFixed(0)}</dd>
          <small>fatigue</small>
        </div>
        <div>
          <dt>
            <i className="swatch line dash" />
            Form
          </dt>
          <dd>{signed(f.tsb)}</dd>
          <small>into today</small>
        </div>
      </dl>
      <FitChart F={F} tall={compact ? 150 : 200} />
      <details className="how">
        <summary>How it's computed</summary>
        <p>
          Daily load units from the HR model: fitness (CTL) and fatigue (ATL) are its long and short averages, and form
          is yesterday's CTL − ATL, as in the TrainingPeaks PMC. The shape carries the information; the absolute numbers
          depend on the load model.
        </p>
      </details>
    </section>
  );
}
