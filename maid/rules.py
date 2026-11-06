"""
    Desc: Rules to find empty row(s), duplicate(s) and error value(s)
    Creator: Kirosha
"""

from typing import Callable

from maid.models import Table, Removal

# markers of a broken cell
ERROR_MARKERS = frozenset({
    "", "null", "none", "nan", "na", "n/a", "#n/a", "#ref!",
    "#value!", "#div/0!", "#name?", "#num!", "error", "err",
    "undefined", "inf", "-inf"
})

# markers of a missing cell
NULLISH = frozenset({"", "null", "none", "nan", "na", "n/a"})

# the order is fixed: a row is removed by the first rule that matched it
ALL_RULES = ("empty", "duplicates", "errors")

def _normalize(value: str) -> str:
    return value.strip().lower()

def _is_nullish(value: str) -> bool:
    return _normalize(value) in NULLISH

def _is_error_like(value: str) -> bool:
    return _normalize(value) in ERROR_MARKERS

def is_number(value: str) -> bool:
    try:
        float(value.strip())
        return True
    except ValueError:
        return False

def rule_empty(table: Table, index: int, row: dict[str, str]) -> Removal | None:
    if all(_is_nullish(row.get(column, "")) for column in table.columns):
        return Removal(row_index=index, rule="empty", reason="все ячейки пустые", row=row)

def rule_errors(table: Table, index: int, row: dict[str, str]) -> Removal | None:
    bad = []

    for column in table.columns:
        value = row.get(column, "")

        # blank cell is a missing value, not an error value
        if not value.strip(): continue

        if _is_error_like(value):
            bad.append(column)
        elif column in table.numeric_columns and not is_number(value):
            bad.append(column)

    if bad:
        return Removal(row_index=index, rule="errors", reason=f"ошибочные значения: {', '.join(bad)}", row=row)

# row rules, "duplicates" is implemented in apply_rules because it needs a state
RULES: dict[str, Callable] = {
    "empty": rule_empty,
    "errors": rule_errors
}

def apply_rules(table: Table, rules: list[str] | tuple[str, ...]) -> tuple[Table, list[Removal], dict[str, int]]:
    unknown = [rule for rule in rules if rule not in ALL_RULES]
    if unknown: raise SystemExit(f"Неизвестное правило: {', '.join(unknown)}. Доступные: {', '.join(ALL_RULES)}")

    active = [rule for rule in ALL_RULES if rule in rules]
    stats = {rule: 0 for rule in active}

    # only accepted rows get here
    seen: set[tuple] = set()
    kept_rows = []
    removed = []

    for index, row in enumerate(table.rows):
        key = tuple(row.get(column, "") for column in table.columns)
        removal = None

        for rule in active:
            if rule == "duplicates":
                if key in seen:
                    removal = Removal(row_index=index, rule=rule, reason="полный дубликат предыдущей строки", row=row)
            else:
                removal = RULES[rule](table, index, row)

            if removal: break

        if removal:
            removed.append(removal)
            stats[removal.rule] += 1
        else:
            seen.add(key)
            kept_rows.append(row)

    kept = Table(
        name=table.name,
        columns=list(table.columns),
        rows=kept_rows,
        numeric_columns=set(table.numeric_columns),
        source_path=table.source_path
    )

    return kept, removed, stats
