"""
    Desc: Models to describe table, removed row(s) and cleaning result
    Creator: Kirosha
"""

from dataclasses import dataclass, field

@dataclass
class Table:
    name: str
    columns: list[str]
    # all values are strings, None is always normalized to ""
    rows: list[dict[str, str]]
    numeric_columns: set[str] = field(default_factory=set)
    source_path: str | None = None

@dataclass
class Removal:
    # 0-based index in the source table (header is not counted)
    row_index: int
    rule: str
    reason: str
    row: dict[str, str]

@dataclass
class CleanResult:
    kept: Table
    removed: list[Removal]
    stats: dict[str, int]
