"""Durable, per-subject progress report.

The report doubles as the pipeline's state machine: each subject row records the
node it should run next (``node``, used to resume after a crash or a re-run) and
a numeric ``status`` (the ordinal of the last completed step, negative on error).

It is written in the column-oriented shape MedPerf already understands
(``pandas.DataFrame(report_dict)`` with a ``status`` column), so the existing
``ReportSender`` ships progress with no changes on the MedPerf side.
"""

from __future__ import annotations

import os
import threading
from typing import Dict, List, Optional

import yaml

DONE = "DONE"
_COLUMNS = ["status", "status_name", "comment", "node", "data_path", "labels_path"]


class Report:
    def __init__(self, report_path: str):
        self._path = report_path
        self._lock = threading.RLock()
        self._rows: Dict[str, Dict] = {}

    # ---- loading / persistence -------------------------------------------------
    def load(self) -> None:
        """Populate state from an existing report file, enabling resume."""
        if not self._path or not os.path.exists(self._path):
            return
        with open(self._path) as f:
            data = yaml.safe_load(f) or {}
        subjects = set()
        for col in _COLUMNS:
            subjects.update((data.get(col) or {}).keys())
        with self._lock:
            for subject in subjects:
                self._rows[subject] = {
                    col: (data.get(col) or {}).get(subject) for col in _COLUMNS
                }

    def flush(self) -> None:
        """Atomically write the report to disk in the MedPerf-compatible shape."""
        if not self._path:
            return
        with self._lock:
            columns = {
                col: {s: row.get(col) for s, row in self._rows.items()}
                for col in _COLUMNS
            }
        os.makedirs(os.path.dirname(self._path) or ".", exist_ok=True)
        tmp = self._path + ".tmp"
        with open(tmp, "w") as f:
            yaml.safe_dump(columns, f)
        os.replace(tmp, self._path)

    # ---- mutation --------------------------------------------------------------
    def add_subject(
        self,
        subject: str,
        node: Optional[str] = None,
        data_path: str = "",
        labels_path: str = "",
    ) -> None:
        with self._lock:
            self._rows.setdefault(
                subject,
                {
                    "status": 0,
                    "status_name": "setup",
                    "comment": "",
                    "node": node,
                    "data_path": data_path,
                    "labels_path": labels_path,
                },
            )
        self.flush()

    def set_status(self, subject: str, ordinal: int, name: str) -> None:
        """Record that ``subject`` completed a step (its ordinal/name). The next
        node the subject moves to is set separately via ``set_node``."""
        with self._lock:
            row = self._rows.setdefault(subject, {})
            row.update(status=ordinal, status_name=name, comment="")
        self.flush()

    def set_error(self, subject: str, ordinal: int, name: str, comment: str) -> None:
        with self._lock:
            row = self._rows.setdefault(subject, {})
            row.update(status=-abs(ordinal), status_name=name, comment=comment)
        self.flush()

    def set_node(self, subject: str, node: str) -> None:
        with self._lock:
            self._rows.setdefault(subject, {})["node"] = node
        self.flush()

    def mark_done(self, subject: str) -> None:
        self.set_node(subject, DONE)

    # ---- queries ---------------------------------------------------------------
    def has_subjects(self) -> bool:
        with self._lock:
            return bool(self._rows)

    def subjects(self) -> List[str]:
        with self._lock:
            return list(self._rows.keys())

    def get_node(self, subject: str) -> Optional[str]:
        with self._lock:
            return self._rows.get(subject, {}).get("node")

    def is_done(self, subject: str) -> bool:
        return self.get_node(subject) == DONE
