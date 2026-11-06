"""
    Desc: Readers to load table(s) from .csv/.tsv and SQLite file(s)
    Creator: Kirosha
"""

import csv
import sqlite3
from pathlib import Path

from maid.models import Table
from maid.rules import NULLISH, is_number

CSV_SUFFIXES = (".csv", ".tsv")
SQLITE_SUFFIXES = (".db", ".sqlite", ".sqlite3")
SUPPORTED_SUFFIXES = CSV_SUFFIXES + SQLITE_SUFFIXES

# declared types of SQLite columns that are treated as numeric
NUMERIC_TYPES = ("INT", "REAL", "NUM", "DEC", "FLOAT", "DOUBLE")

def is_sqlite(path: str | Path) -> bool:
    return Path(path).suffix.lower() in SQLITE_SUFFIXES

def __infer_numeric(columns: list[str], rows: list[dict[str, str]]) -> set[str]:
    # csv has no types, so a column is numeric when most of its filled cells are numbers
    numeric = set()

    for column in columns:
        values = [row[column].strip() for row in rows if row[column].strip().lower() not in NULLISH]
        if not values: continue

        if sum(is_number(value) for value in values) / len(values) > 0.5:
            numeric.add(column)

    return numeric

def read_csv(path: str | Path) -> Table:
    path = Path(path)
    fallback = csv.excel_tab if path.suffix.lower() == ".tsv" else csv.excel

    with open(path, "r", encoding="utf-8-sig", newline="") as file:
        sample = file.read(4096)
        file.seek(0)

        try:
            dialect = csv.Sniffer().sniff(sample, delimiters=",;\t")
        except csv.Error:
            dialect = fallback

        reader = csv.DictReader(file, dialect=dialect)
        columns = [name.strip() for name in (reader.fieldnames or [])]
        reader.fieldnames = columns

        rows = [
            {column: row.get(column) or "" for column in columns}
            for row in reader
        ]

    return Table(
        name=path.stem,
        columns=columns,
        rows=rows,
        numeric_columns=__infer_numeric(columns, rows),
        source_path=str(path)
    )

def __quote(name: str) -> str:
    return '"' + name.replace('"', '""') + '"'

def read_sqlite(path: str | Path, table: str | None = None) -> Table:
    path = Path(path)

    try:
        connection = sqlite3.connect(path)
        connection.row_factory = sqlite3.Row

        try:
            names = [
                row["name"] for row in connection.execute(
                    "SELECT name FROM sqlite_master WHERE type = 'table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
                )
            ]
            if not names: raise SystemExit(f"В базе {path} нет таблиц")

            if table is None:
                table = names[0]
            elif table not in names:
                raise SystemExit(f"Таблица {table} не найдена в {path}. Доступные: {', '.join(names)}")

            info = connection.execute(f"PRAGMA table_info({__quote(table)})").fetchall()
            columns = [row["name"] for row in info]
            numeric = {
                row["name"] for row in info
                if any(token in (row["type"] or "").upper() for token in NUMERIC_TYPES)
            }

            rows = [
                {column: "" if row[column] is None else str(row[column]) for column in columns}
                for row in connection.execute(f"SELECT * FROM {__quote(table)}")
            ]
        finally:
            connection.close()
    except sqlite3.DatabaseError as err:
        raise SystemExit(f"Ошибка чтения SQLite: {err}")

    return Table(
        name=table,
        columns=columns,
        rows=rows,
        numeric_columns=numeric,
        source_path=str(path)
    )

def read_table(path: str | Path, table: str | None = None) -> Table:
    path = Path(path)
    suffix = path.suffix.lower()

    if suffix not in SUPPORTED_SUFFIXES:
        raise SystemExit(f"Неподдерживаемое расширение {suffix or '(нет)'}. Поддерживаются: {', '.join(SUPPORTED_SUFFIXES)}")
    if not path.is_file(): raise SystemExit(f"Файл не найден: {path}")

    if suffix in SQLITE_SUFFIXES:
        return read_sqlite(path, table)
    return read_csv(path)
