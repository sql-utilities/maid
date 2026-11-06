# maid

Maid чистит табличные данные от пустых строк, дубликатов и ошибочных значений. Читает `.csv` / `.tsv` / `.db` / `.sqlite` / `.sqlite3`, применяет выбранные правила, сохраняет очищенный результат и печатает сводку. Зависимостей нет, только stdlib.

```
data.csv ──► reader ──► rules (empty → duplicates → errors) ──► writer ──► data.cleaned.csv
```

---

## Установка

```
pip install -e .
```

Требуется Python `3.10+`.

## Примеры

```
maid --path testdata/dirty.csv --all --keep-removed
maid --path testdata/dirty.csv --duplicates --errors
maid --path testdata/dirty.csv --rules empty --out /tmp/out.csv
```

Первая команда выведет:

```
строк всего: 8
  удалено (empty): 1
  удалено (duplicates): 1
  удалено (errors): 2
  осталось: 4
результат: testdata/dirty.cleaned.csv
удалённые: testdata/dirty.removed.csv
```

## Флаги

| Флаг | Описание |
|------|----------|
| `--path` | исходный файл (обязательный) |
| `--empty` | удалить строки, где все ячейки пустые |
| `--duplicates` | удалить полные дубликаты, остаётся первое вхождение |
| `--errors` | удалить строки с ошибочными значениями |
| `--all` | все три правила |
| `--rules` | правила через запятую, например `empty,duplicates` |
| `--out` | куда сохранить результат, по умолчанию `<stem>.cleaned<suffix>` |
| `--keep-removed` | сохранить удалённые строки в `<stem>.removed.csv` |
| `--no-report` | не печатать сводку |
| `--table` | таблица SQLite |

Если не указано ни одно правило, утилита завершится с подсказкой.

## Правила

- **empty**: все ячейки строки пустые или `null` / `none` / `nan` / `na` / `n/a` (без учёта регистра).
- **duplicates**: все значения строки совпадают с уже принятой строкой. Удалённые строки в сравнении не участвуют.
- **errors**: в строке есть ячейка из `ERROR_MARKERS` (`#N/A`, `#REF!`, `error`, `inf` и т.д.) или значение в числовой колонке, которое не парсится как число. Пустая ячейка ошибкой не считается: это пропуск, а не сломанное значение.

### Порядок правил

Порядок фиксирован: `empty` → `duplicates` → `errors`, независимо от порядка флагов. Строка удаляется по первому сработавшему правилу, и в статистике учитывается именно оно. Поэтому полностью пустая строка уходит в `empty`, а не в `errors`.

### Числовые колонки

- SQLite: колонка числовая, если declared type содержит `INT`, `REAL`, `NUM`, `DEC`, `FLOAT` или `DOUBLE`.
- CSV/TSV: типов нет, поэтому колонка считается числовой, если больше половины её заполненных ячеек являются числами. В `testdata/dirty.csv` так определяется колонка `age`, и значение `abc` попадает в `errors`.

## Файл с удалёнными строками

С `--keep-removed` рядом с исходником создаётся `<stem>.removed.csv`. К колонкам таблицы добавляются три служебные: `__row_index__` (0-based индекс в исходной таблице без заголовка), `__rule__` и `__reason__`. Файл создаётся только если что-то было удалено.

## SQLite

`--table` необязателен: по умолчанию берётся первая таблица по имени. Результат для SQLite сохраняется в CSV (`<stem>.cleaned.csv`), исходная база не меняется.

## Структура проекта

```
maid/
├── pyproject.toml
├── README.md
├── maid/
│   ├── __init__.py          ← __version__
│   ├── models.py            ← Table, Removal, CleanResult
│   ├── readers.py           ← read_csv, read_sqlite
│   ├── rules.py             ← маркеры, правила, apply_rules
│   ├── writers.py           ← write_csv, write_removed_csv, default_out_path
│   └── cli.py               ← argparse, main()
└── testdata/
    ├── dirty.csv
    ├── expected_cleaned.csv
    └── expected_removed.csv
```

## Как добавить своё правило

1. В `maid/rules.py` написать функцию `rule_xxx(table, index, row) -> Removal | None`.
2. Добавить её в `RULES` и имя в `ALL_RULES` (порядок в `ALL_RULES` задаёт порядок применения).
3. В `maid/cli.py` добавить флаг `--xxx` в `_build_parser`.
4. `_parse_rules` подхватит флаг сам: он берёт значения из `ALL_RULES` через `getattr(args, rule)`.

## Проверка

```
pip install -e .
maid --path testdata/dirty.csv --all --keep-removed
diff testdata/dirty.cleaned.csv testdata/expected_cleaned.csv && echo OK
diff testdata/dirty.removed.csv testdata/expected_removed.csv && echo OK
```
# maid
