"""The training diary: one derived entry per week — day log, plan comparison, verdicts."""

import datetime as dt
from typing import TYPE_CHECKING

from tl import config, plan
from tl.data import runs_first
from tl.periods import monotony
from tl.render import hmm

if TYPE_CHECKING:
    from tl.data import Activity
    from tl.periods import Week

DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]


class Entry:
    def __init__(
        self,
        week: Week,
        fitness: dict[dt.date, dict[str, float]],
        load: dict[dt.date, float],
    ) -> None:
        self.week = week
        self.plan = plan.week_for(week.start)
        self.flags = week.flags()
        self.mono = monotony(load, week)
        f = fitness.get(min(week.end, config.TODAY))
        # A finished week reports the form it hands to the next Monday: its closing CTL - ATL.
        self.fitness = {**f, "tsb": f["ctl"] - f["atl"]} if f and week.end < config.TODAY else f

    def days(self) -> list[tuple[str, dt.date, list[Activity]]]:
        dates = [self.week.start + dt.timedelta(days=i) for i in range(7)]
        return [
            (DAYS[d.weekday()], d, runs_first(a for a in self.week.acts if a.date == d))
            for d in dates
        ]

    def headline(self) -> str:
        w = self.week
        if not w.acts:
            return "No training recorded."
        bits = [
            (
                f"{hmm(w.total_h)} total · {hmm(w.run_h)} run "
                f"({w.run_km:.0f} km, {w.run_vert:.0f} m, {w.density:.0f} m/h)"
            )
        ]
        if w.bike_h >= 0.5:
            bits.append(f"{hmm(w.bike_h)} bike")
        if w.gym_h >= 0.4:
            bits.append(f"{hmm(w.gym_h)} gym")
        return " · ".join(bits)

    def _plan_notes(self) -> list[str]:
        """How the finished week read against its plan targets."""
        out, w, p = [], self.week, self.plan
        if p and not w.partial:
            if p.run_h:
                r = w.run_h / p.run_h
                if r < 0.85:
                    out.append(f"Running {(1 - r) * 100:.0f}% under the {p.run_h:.1f} h target.")
                elif r > 1.15:
                    out.append(f"Running {(r - 1) * 100:.0f}% over the {p.run_h:.1f} h target.")
                else:
                    out.append(f"Running on target ({w.run_h:.1f} vs {p.run_h:.1f} h).")
            if p.bike_h and w.bike_h / p.bike_h < 0.6:
                out.append(
                    f"Bike well short — {w.bike_h:.1f} of {p.bike_h:.1f} h. That is the plan's "
                    f"aerobic ballast; running cannot absorb it instead."
                )
            if p.gym_h and w.gym_h < 0.4:
                out.append(f"No gym logged against a {p.gym_h:.1f} h target (R5).")
        return out

    def notes(self) -> list[str]:
        out, w = self._plan_notes(), self.week
        lr = w.longest_run
        if lr:
            out.append(
                f"Longest run {hmm(lr.mins / 60)} / {lr.km:.1f} km / "
                f"{lr.vert:.0f} m on {DAYS[lr.date.weekday()]}."
            )
        if w.back_to_back:
            out.append("Back-to-back long days achieved — the Chianti-specific stimulus.")
        elif self.plan and self.plan.weekend.startswith(("A", "C")) and not w.partial:
            out.append("No back-to-back long days; the plan called for them.")

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
            verdict = "above" if w.density >= config.VERT_FLOOR else "below"
            out.append(
                f"Vert density {w.density:.0f} m/h — {verdict} the {config.VERT_FLOOR} m/h floor."
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

    def highlights(self) -> list[tuple[dt.date, str | None, str]]:
        """Dan's session notes for the week."""
        return [
            (a.date, a.name, a.note) for a in sorted(self.week.acts, key=lambda a: a.date) if a.note
        ]
