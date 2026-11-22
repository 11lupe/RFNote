#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""为 3GPP 规范（按章节拆分的多个 docx）重建章节索引 CSV。

产物：
- ``05 3GPP规范/<规范号>/章节索引.csv``
- ``05 3GPP规范/检索总表.csv``

用法（在仓库根目录执行）::

    python tools/index_3gpp.py           # 重建全部索引
    python tools/index_3gpp.py --check   # 只比对，不写文件；不一致时退出码 1
    python tools/index_3gpp.py --root "05 3GPP规范"

依赖：``python-docx``（``pip install python-docx``）。旧 ``.doc`` 需先转成
``docs_docx/*.docx``，本脚本只扫描转换后的文件。
"""
from __future__ import annotations

import argparse
import csv
import re
import sys
from pathlib import Path

try:
    from docx import Document
except ImportError:  # pragma: no cover
    sys.exit("缺少依赖 python-docx：pip install python-docx")

ROOT = Path(__file__).resolve().parents[1] / "05 3GPP规范"

NUM_RE = re.compile(r"^(\d+(?:\.\d+){0,4})\s+(\S.{0,110})$")
ANNEX_RE = re.compile(r"^(Annex\s+[A-Z][0-9]?)\s*(.{0,100})$")
ANNEX_NUM_RE = re.compile(r"^([A-Z]\.\d+(?:\.\d+){0,3})\s+(\S.{0,110})$")
SPEC_RE = re.compile(r"^\d{2}\.\d{3}")

NOISE = (
    "3gpp", "release", "etsi", "ts 3", "ts 5", "©", "copyright",
    "postal address", "office address", "email", "http",
    "route des lucioles", "sophia antipolis", "presented to tsg",
    "or greater indicates", "tsg approved", "change control",
    "the present document", "informative", "void",
)


def is_noise(text: str) -> bool:
    t = text.strip()
    if not t or len(t) > 130:
        return True
    low = t.lower()
    return any(bad in low for bad in NOISE)


def clean_title(text: str) -> str:
    """去掉目录行尾的 Tab + 页码。"""
    return re.sub(r"\t+\s*\d+\s*$", "", text).strip()


def clause_key(clause: str) -> tuple[int, list[int], str]:
    """数字条款按层级排，Annex 条款排在数字之后。"""
    m = re.match(r"^(\d+(?:\.\d+)*)", clause)
    if m:
        return (0, [int(part) for part in m.group(1).split(".")], clause)
    return (1, [], clause)


def scan_docx(path: Path, spec: str, rows: list[tuple[str, str, str, str]]) -> None:
    base = path.name
    if "cover" in base.lower():
        return  # 封面/目录文件跳过，避免与正文重复
    try:
        doc = Document(str(path))
    except Exception as exc:  # noqa: BLE001
        print(f"  SKIP {base}: {exc}")
        return
    seen: set[tuple[str, str]] = set()
    for p in doc.paragraphs:
        t = clean_title(p.text.strip())
        if not t or is_noise(t):
            continue
        m = NUM_RE.match(t)
        if m:
            clause, title = m.group(1), m.group(2).strip()
            if len(clause.split(".")) <= 4 and (clause, title) not in seen:
                seen.add((clause, title))
                rows.append((spec, base, clause, title))
            continue
        m = ANNEX_RE.match(t)
        if m and len(m.group(2).strip()) < 100:
            key = (m.group(1), m.group(2).strip())
            if key not in seen:
                seen.add(key)
                rows.append((spec, base, m.group(1), m.group(2).strip() or "(annex)"))
            continue
        m = ANNEX_NUM_RE.match(t)
        if m:
            key = (m.group(1), m.group(2).strip())
            if key not in seen:
                seen.add(key)
                rows.append((spec, base, m.group(1), m.group(2).strip()))


def build(root: Path, write: bool) -> list[tuple[str, str, str, str]]:
    specs = sorted(d for d in root.iterdir() if d.is_dir() and SPEC_RE.match(d.name))
    all_rows: list[tuple[str, str, str, str]] = []
    for spec_dir in specs:
        docs = spec_dir / "docs"
        if not docs.is_dir():
            print(f"{spec_dir.name}: no docs dir, skip")
            continue
        docx_files = sorted(p for p in docs.iterdir() if p.suffix.lower() == ".docx")
        doc_files = sorted(p for p in docs.iterdir() if p.suffix.lower() == ".doc")
        rows: list[tuple[str, str, str, str]] = []
        for path in docx_files:
            scan_docx(path, spec_dir.name, rows)
        converted = spec_dir / "docs_docx"
        conv_files = (
            sorted(p for p in converted.iterdir() if p.suffix.lower() == ".docx")
            if converted.is_dir() else []
        )
        for path in conv_files:
            scan_docx(path, spec_dir.name, rows)
        rows.sort(key=lambda r: clause_key(r[2]))
        if write:
            write_rows(spec_dir / "章节索引.csv", rows)
        print(
            f"{spec_dir.name}: docx={len(docx_files)} doc={len(doc_files)} "
            f"conv={len(conv_files)} clauses={len(rows)}"
        )
        all_rows.extend(rows)
    all_rows.sort(key=lambda r: (r[0], clause_key(r[2])))
    if write:
        write_rows(root / "检索总表.csv", all_rows)
    print("TOTAL", len(all_rows))
    return all_rows


def write_rows(path: Path, rows: list[tuple[str, str, str, str]]) -> None:
    with open(path, "w", encoding="utf-8-sig", newline="") as fh:
        writer = csv.writer(fh, lineterminator="\n")
        writer.writerow(["规范", "文件", "条款", "标题"])
        writer.writerows(rows)


def read_total(path: Path) -> list[tuple[str, ...]]:
    with open(path, encoding="utf-8-sig", newline="") as fh:
        reader = csv.reader(fh)
        next(reader, None)
        return [tuple(row) for row in reader]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="重建 3GPP 章节索引")
    parser.add_argument("--root", type=Path, default=ROOT, help="规范库根目录")
    parser.add_argument("--check", action="store_true", help="只比对，不写文件")
    args = parser.parse_args(argv)

    if not args.root.is_dir():
        parser.error(f"目录不存在：{args.root}")

    expected = build(args.root, write=not args.check)
    if not args.check:
        return 0

    actual = read_total(args.root / "检索总表.csv")
    if len(expected) != len(actual):
        print(f"MISMATCH total: expected {len(expected)}, csv {len(actual)}")
        return 1
    for index, (want, got) in enumerate(zip(expected, actual), start=1):
        if want != got:
            print(f"MISMATCH row {index}: expected {want}, csv {got}")
            return 1
    print(f"OK total={len(expected)}（检索总表.csv 与重新扫描结果一致）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
