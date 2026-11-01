"""The training diary: one entry per week, built from the cache, not by hand.

An entry is the week's day-by-day log, its plan comparison, its guardrail
flags, and a short verdict assembled from whichever of those actually said
something. Nothing here is written prose from a human — it is derived, so it
stays true when the data is topped up.
"""

import datetime as dt

from . import config as C
from . import plan
from .periods import monotony

DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]


def _fmt_h(x):
    return f"{int(x)}:{round((x % 1) * 60):02d}"


class Entry:
    def __init__(self, ds, week, fitness):
        self.week = week
        self.plan = plan.week_for(week.start)
        self.cmp = plan.compare(week, self.plan)
        self.flags = week.flags()
        self.mono, self.strain = monotony(ds, week)
        self.fitness = fitness.get(min(week.end, C.TODAY))
        self.aero = week.hr_at_pace()

    # ------------------------------------------------------------- day view
    def days(self):
        out = []
        for i in range(7):
            d = self.week.start + dt.timedelta(days=i)
            acts = sorted(
                [a for a in self.week.acts if a.date == d],
                key=lambda a: (a.group != "run", -a.mins),
            )
            out.append((DAYS[i], d, acts))
        return out

    # ------------------------------------------------------------- verdicts
    def headline(self):
        w = self.week
        if not w.acts:
            return "No training recorded."
        bits = [
            f"{_fmt_h(w.total_h)} total · {_fmt_h(w.run_h)} run "
            f"({w.run_km:.0f} km, {w.run_vert:.0f} m, {w.density:.0f} m/h)"
        ]
        if w.bike_h >= 0.5:
            bits.append(f"{_fmt_h(w.bike_h)} bike")
        if w.gym_h >= 0.4:
            bits.append(f"{_fmt_h(w.gym_h)} gym")
        return " · ".join(bits)

    def notes(self):
        """The verdict lines — each one earns its place or is not emitted."""
        out, w, c = [], self.week, self.cmp
        if c and not w.partial:
            r = c["run_h"][2]
            if r is not None:
                if r < 0.85:
                    out.append(
                        f"Running {(1 - r) * 100:.0f}% under the {c['run_h'][1]:.1f} h target."
                    )
                elif r > 1.15:
                    out.append(
                        f"Running {(r - 1) * 100:.0f}% over the {c['run_h'][1]:.1f} h target."
                    )
                else:
                    out.append(f"Running on target ({w.run_h:.1f} vs {c['run_h'][1]:.1f} h).")
            if c["bike_h"][1] and c["bike_h"][2] is not None and c["bike_h"][2] < 0.6:
                out.append(
                    f"Bike well short — {w.bike_h:.1f} of "
                    f"{c['bike_h'][1]:.1f} h. That is the plan's aerobic "
                    f"ballast; running cannot absorb it instead."
                )
            if c["gym_h"][1] and w.gym_h < 0.4:
                out.append(f"No gym logged against a {c['gym_h'][1]:.1f} h target (R5).")

        lr = w.longest_run
        if lr:
            out.append(
                f"Longest run {_fmt_h(lr.mins / 60)} / {lr.km:.1f} km / "
                f"{lr.vert:.0f} m on {DAYS[lr.date.weekday()]}."
            )
        if w.back_to_back:
            out.append("Back-to-back weekend achieved — the Chianti-specific stimulus.")
        elif self.plan and self.plan.weekend.startswith(("A", "C")) and not w.partial:
            out.append("Weekend was a single long run; the plan called for a back-to-back.")

        q = w.quality
        if q:
            out.append(
                "Quality: "
                + ", ".join(
                    f"{a.type} on {DAYS[a.date.weekday()]}" + (f" — {a.name}" if a.name else "")
                    for a in q
                )
            )
        if w.density and w.run_h > 4:
            verdict = "above" if w.density >= C.VERT_FLOOR else "below"
            out.append(
                f"Vert density {w.density:.0f} m/h — {verdict} the {C.VERT_FLOOR} m/h floor."
            )
        if self.mono and self.mono > 2.0:
            out.append(
                f"Monotony {self.mono:.1f} — the week was too evenly hard; "
                f"Foster's threshold for trouble is 2.0."
            )
        if w.mean_feel is not None:
            out.append(f"Self-reported feel {w.mean_feel:+.1f} over {len(w.feels)} scored runs.")
        for code, msg in self.flags:
            out.append(f"[{code}] {msg}")
        return out

    def highlights(self):
        """Session notes worth keeping — the human texture, from Strava."""
        return [
            (a.date, a.name, a.note) for a in sorted(self.week.acts, key=lambda a: a.date) if a.note
        ]


def build(ds, weeks, fitness):
    return [Entry(ds, w, fitness) for w in weeks]
