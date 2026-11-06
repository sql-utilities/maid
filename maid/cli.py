"""
    Desc: CLI to parse argument(s), run cleaning and print report
    Creator: Kirosha
"""

import sys
import argparse
from pathlib import Path

from maid import __version__
from maid.models import CleanResult
from maid.readers import read_table, is_sqlite
from maid.rules import ALL_RULES, apply_rules
from maid.writers import default_out_path, write_csv, write_removed_csv

HINT = "Укажите хотя бы одно правило: --empty, --duplicates, --errors, --rules empty,duplicates или --all"

def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="maid",
        description="Чистит таблицу от пустых строк, дубликатов и ошибочных значений"
    )

    parser.add_argument("--path", required=True, help="путь к .csv / .tsv / .db / .sqlite / .sqlite3")
    parser.add_argument("--table", help="таблица SQLite (по умолчанию первая по имени)")
    parser.add_argument("--all", action="store_true", help="все правила: empty, duplicates, errors")
    parser.add_argument("--empty", action="store_true", help="удалить полностью пустые строки")
    parser.add_argument("--duplicates", action="store_true", help="удалить полные дубликаты")
    parser.add_argument("--errors", action="store_true", help="удалить строки с ошибочными значениями")
    parser.add_argument("--rules", help="правила через запятую, например empty,duplicates")
    parser.add_argument("--out", help="куда сохранить результат (по умолчанию <stem>.cleaned<suffix>)")
    parser.add_argument("--keep-removed", action="store_true", help="сохранить удалённые строки в <stem>.removed.csv")
    parser.add_argument("--no-report", action="store_true", help="не печатать сводку")
    parser.add_argument("--version", action="version", version=f"maid {__version__}")

    return parser

def _parse_rules(args: argparse.Namespace) -> list[str]:
    if args.all: return list(ALL_RULES)

    rules = [rule for rule in ALL_RULES if getattr(args, rule)]

    if args.rules:
        for rule in args.rules.split(","):
            rule = rule.strip()
            if rule and rule not in rules:
                rules.append(rule)

    if not rules: raise SystemExit(HINT)
    return rules

def _print_report(total: int, stats: dict[str, int], out_path: Path, removed_path: Path | None) -> None:
    print(f"строк всего: {total}")

    for rule in ALL_RULES:
        if rule in stats:
            print(f"  удалено ({rule}): {stats[rule]}")

    print(f"  осталось: {total - sum(stats.values())}")
    print(f"результат: {out_path}")

    if removed_path:
        print(f"удалённые: {removed_path}")

def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    rules = _parse_rules(args)

    source = Path(args.path)
    table = read_table(source, args.table)

    if not table.rows:
        print(f"В таблице {table.name} нет строк", file=sys.stderr)
        return 1

    result = CleanResult(*apply_rules(table, rules))

    if args.out:
        out_path = Path(args.out)
    else:
        out_path = default_out_path(source)
        # sqlite result is saved as csv
        if is_sqlite(source): out_path = out_path.with_suffix(".csv")

    if out_path.resolve() == source.resolve():
        raise SystemExit("Результат не может перезаписывать исходный файл, укажите другой --out")

    write_csv(result.kept, out_path)

    removed_path = None
    if args.keep_removed and result.removed:
        removed_path = default_out_path(source, ".removed").with_suffix(".csv")
        write_removed_csv(result.removed, removed_path, table.columns)

    if not args.no_report:
        _print_report(len(table.rows), result.stats, out_path, removed_path)

    return 0

if __name__ == "__main__":
    sys.exit(main())
