"""tl — builds the Chianti 120K diary page's data.

uv run tl site [path]         write web/src/payload.json for the diary page
"""

import json
import sys
from pathlib import Path

from tl import config, diary, export
from tl.data import Dataset
from tl.periods import build_months, build_seasons, build_weeks, fitness_curve


def site(out: Path) -> str:
    """Write the diary page's payload.

    Pages cannot run tl (the CSVs never leave this machine), so the React app
    builds from this committed file. The diary starts the week before the
    macrocycle opens, so the entries lead in with week 1's setup.
    """
    ds = Dataset.load()
    load = ds.daily_load()
    weeks = build_weeks(ds)
    fitness = fitness_curve(ds, load)
    entries = [diary.Entry(w, fitness, load) for w in weeks]
    obj = export.web_payload(ds, weeks, entries, build_months(ds), build_seasons(ds), fitness)
    with open(out, "w") as fh:
        json.dump(obj, fh, ensure_ascii=False, indent=1)
        fh.write("\n")
    return (
        f"wrote {out}  ({out.stat().st_size // 1024} KB, "
        f"{len(obj['diary'])} diary weeks, {len(obj['months'])} months)"
    )


def main(argv: list[str] | None = None) -> int:
    argv = list(argv if argv is not None else sys.argv[1:])
    if not argv or argv[0] != "site" or len(argv) > 2:
        print(__doc__)
        return 0 if argv and argv[0] in ("-h", "--help", "help") else 1
    out = Path(argv[1]) if len(argv) == 2 else config.DATA.parent / "web" / "src" / "payload.json"
    print(site(out))
    return 0
