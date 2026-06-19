"""
history.py — Module 2: User history lookup.

Loads user_history.csv once and provides a by-user_id lookup returning parsed
flags (list[str]) and a free-text summary. Zero model calls; no verdict logic.
"""

from dataclasses import dataclass, field

from pipeline.io_utils import load_user_history


@dataclass
class HistoryRecord:
    flags: list[str] = field(default_factory=list)
    summary: str = ""


_MISSING = HistoryRecord(flags=[], summary="")


class HistoryLookup:
    """Loads user_history.csv once; get() never raises on unknown user_id."""

    def __init__(self) -> None:
        self._index: dict[str, HistoryRecord] = {}
        for row in load_user_history():
            uid = row["user_id"].strip()
            raw_flags = row["history_flags"].strip()
            if raw_flags and raw_flags.lower() != "none":
                flags = [f.strip() for f in raw_flags.split(";") if f.strip()]
            else:
                flags = []
            self._index[uid] = HistoryRecord(
                flags=flags,
                summary=row["history_summary"].strip(),
            )

    def get(self, user_id: str) -> HistoryRecord:
        return self._index.get(user_id.strip(), _MISSING)
