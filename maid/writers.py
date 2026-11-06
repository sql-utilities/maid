"""
    Desc: Writers to save cleaned and removed row(s) to .csv/.tsv file(s)
    Creator: Kirosha
"""

import csv
from pathlib import Path

from maid.models import Table, Removal

# service columns of the removed file
REMOVED_COLUMNS = ["__row_index__", "__rule__", "__reason__"]

def default_out_path(source: str | Path, suffix: str = ".cleaned") -> Path:
    source = Path(source)
    return source.with_name(f"{source.stem}{suffix}{source.suffix}")

def write_csv(table: Table, path: str | Path) -> None:
    path = Path(path)
    delimiter = "\t" if path.suffix.lower() == ".tsv" else ","

    with open(path, "w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=table.columns, delimiter=delimiter, lineterminator="\n")
        writer.writeheader()
        writer.writerows(table.rows)

def write_removed_csv(removed: list[Removal], path: str | Path, columns: list[str]) -> None:
    with open(path, "w", encoding="utf-8", newline="") as file:
        writer = csv.writer(file, lineterminator="\n")
        writer.writerow([*REMOVED_COLUMNS, *columns])

        for item in removed:
            writer.writerow([
                item.row_index,
                item.rule,
                item.reason,
                *(item.row.get(column, "") for column in columns)
            ])
