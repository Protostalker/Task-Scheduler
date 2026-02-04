from __future__ import annotations
import re

TASK_CODE_RE = re.compile(r"^T(\d{6})$")

def parse_task_code(code: str) -> int | None:
    m = TASK_CODE_RE.match(code.strip())
    if not m:
        return None
    return int(m.group(1))

def format_task_code(num: int) -> str:
    return f"T{num:06d}"
