#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""RFNote 仓库自检：链接、frontmatter、索引计数、3GPP 索引一致性。

用法（仓库根目录）::

    python tools/repo/check.py

检查项：
1. 所有 Markdown 相对链接可解析（跳过 http/https/mailto/锚点）。
2. 域目录内每篇笔记都有 ``域/...`` 标签的 frontmatter。
3. Markdown 基名全库唯一（Obsidian wikilink 依赖）。
4. 01–02 域索引的「共 N 篇」与 README 目录表一致。
5. 03 规范与标准/3GPP：每个规范目录有 docs / 章节索引.csv，
   各章节索引行数之和等于 ``检索总表.csv``，且与索引里的规范清单一致。
   （原始 zip 不入库，按需用 ``tools/3gpp/fetch.py`` 下载，故不参与校验。）
6. 不再引用旧脚本名（``_fetch.py`` / ``_index.py``）和本机绝对路径。

只读脚本，不修改任何文件；发现问题时退出码 1。
"""
from __future__ import annotations

import csv
import re
import sys
import urllib.parse
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DOMAINS = ["01 基础概念", "02 测试指标", "03 规范与标准"]
SPEC_RE = re.compile(r"^\d{2}\.\d{3}")
EXCLUDE_DIRS = {".git", ".github", ".acl-recovery", "_local", "__pycache__", "node_modules", ".obsidian", "assets"}
LINK_RE = re.compile(r"\]\(\s*(<[^>\n]*>|[^)\s]+)")
COUNT_RE = re.compile(r"共\s*\*\*(\d+)\*\*\s*篇")
ABSOLUTE_RE = re.compile(r"(?:[A-Za-z]:[\\/](?:Users|Project)|/home/|/Users/)")
STALE_SCRIPT_RE = re.compile(r"_(?:fetch|index)\.py")

problems: list[str] = []


def add(message: str) -> None:
    problems.append(message)


def md_files() -> list[Path]:
    files: list[Path] = []
    for path in ROOT.rglob("*.md"):
        if any(part in EXCLUDE_DIRS for part in path.relative_to(ROOT).parts):
            continue
        files.append(path)
    return sorted(files)


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def check_links(files: list[Path]) -> None:
    for md in files:
        text = md.read_text(encoding="utf-8")
        for match in LINK_RE.finditer(text):
            target = match.group(1).strip()
            if target.startswith("<") and target.endswith(">"):
                target = target[1:-1]
            if not target or target.startswith(("#", "http://", "https://", "mailto:", "tel:")):
                continue
            target = urllib.parse.unquote(target.split("#", 1)[0]).strip()
            if not target:
                continue
            if "\\" in target:
                add(f"{rel(md)}: 链接使用反斜杠，应改为 / -> {target}")
                continue
            resolved = (md.parent / target).resolve()
            if not resolved.exists():
                add(f"{rel(md)}: 死链 -> {target}")


def frontmatter_tags(path: Path) -> list[str]:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---"):
        return []
    parts = text.split("---", 2)
    if len(parts) < 3:
        return []
    return [line.strip().lstrip("-").strip() for line in parts[1].splitlines() if line.strip()]


def check_tags(files: list[Path]) -> None:
    for md in files:
        parts = md.relative_to(ROOT).parts
        if not parts or parts[0] not in DOMAINS:
            continue  # README / AGENTS / 命名规范 / tools 说明不是域笔记
        tags = frontmatter_tags(md)
        if not tags:
            add(f"{rel(md)}: 缺 frontmatter 标签")
            continue
        if not any(tag.startswith("域/") for tag in tags):
            add(f"{rel(md)}: frontmatter 缺少 域/... 标签")


def check_basenames(files: list[Path]) -> None:
    groups: dict[str, list[Path]] = defaultdict(list)
    for md in files:
        groups[md.name.casefold()].append(md)
    for name, paths in sorted(groups.items()):
        if name == "readme.md":
            continue  # README 是惯例入口名，允许多层目录各有一份
        if len(paths) > 1:
            add(f"Markdown 基名重复 {name}: " + ", ".join(rel(p) for p in paths))


def check_index_counts() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    readme_counts: dict[str, int] = {}
    for line in readme.splitlines():
        if not line.startswith("| [0"):
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if len(cells) < 3 or not cells[-1].isdigit():
            continue
        domain = re.search(r"\[(\d{2} [^\]]+)\]", cells[0])
        if domain:
            readme_counts[domain.group(1)] = int(cells[-1])

    for name in DOMAINS[:2]:
        domain = ROOT / name
        indices = sorted(domain.glob("00 *索引.md"))
        if len(indices) != 1:
            add(f"{name}: 应有且仅有 1 个 00 *索引.md，实际 {len(indices)}")
            continue
        text = indices[0].read_text(encoding="utf-8")
        declared = COUNT_RE.search(text)
        actual = len([p for p in domain.glob("*.md") if p != indices[0]])
        if not declared:
            add(f"{name}: 索引缺「共 N 篇」")
        elif int(declared.group(1)) != actual:
            add(f"{name}: 索引声明 {declared.group(1)} 篇，实际 {actual} 篇")
        if name in readme_counts and readme_counts[name] != actual:
            add(f"README: {name} 标 {readme_counts[name]} 篇，实际 {actual} 篇")

    total_notes = sum(
        len([p for p in (ROOT / name).glob("*.md") if not p.name.startswith("00 ")])
        for name in DOMAINS[:2]
    )
    declared_total = re.search(r"规模：\*\*(\d+)\*\*\s*篇主题笔记", readme)
    if declared_total and int(declared_total.group(1)) != total_notes:
        add(f"README: 声明 {declared_total.group(1)} 篇主题笔记，实际 {total_notes} 篇")
    index_count = sum(len(list((ROOT / name).glob("00 *索引.md"))) for name in DOMAINS)
    declared_indexes = re.search(r"\*\*(\d+)\*\*\s*个域索引", readme)
    if declared_indexes and int(declared_indexes.group(1)) != index_count:
        add(f"README: 声明 {declared_indexes.group(1)} 个域索引，实际 {index_count} 个")


def csv_rows(path: Path) -> int:
    with open(path, encoding="utf-8-sig", newline="") as fh:
        return max(sum(1 for _ in csv.reader(fh)) - 1, 0)


def check_3gpp() -> None:
    base = ROOT / "03 规范与标准/3GPP"
    total_csv = base / "检索总表.csv"
    if not total_csv.exists():
        add("03 规范与标准/3GPP: 缺 检索总表.csv")
        return
    spec_dirs = sorted(d.name for d in base.iterdir() if d.is_dir() and SPEC_RE.match(d.name))
    total = csv_rows(total_csv)
    counted = 0
    for spec in spec_dirs:
        spec_dir = base / spec
        if not (spec_dir / "docs").is_dir():
            add(f"03 规范与标准/3GPP/{spec}: 缺 docs/")
        chapter = spec_dir / "章节索引.csv"
        if not chapter.exists():
            add(f"03 规范与标准/3GPP/{spec}: 缺 章节索引.csv")
        else:
            counted += csv_rows(chapter)
    if counted != total:
        add(f"3GPP 索引: 各章节索引合计 {counted} 行，检索总表 {total} 行")

    index = base / "00 3GPP检索索引.md"
    if index.exists():
        text = index.read_text(encoding="utf-8")
        manifest = set(re.findall(r"^\| TS (\d{2}\.\d{3}(?:-\d+)?) \|", text, re.M))
        if manifest != set(spec_dirs):
            missing = sorted(set(spec_dirs) - manifest)
            extra = sorted(manifest - set(spec_dirs))
            if missing:
                add(f"03 规范与标准/3GPP/00 3GPP检索索引.md: 规范清单缺 {', '.join(missing)}")
            if extra:
                add(f"03 规范与标准/3GPP/00 3GPP检索索引.md: 清单多出 {', '.join(extra)}")
        if str(total) not in text:
            add(f"03 规范与标准/3GPP/00 3GPP检索索引.md: 未提到总行数 {total}")

        fetch = ROOT / "tools" / "3gpp" / "fetch.py"
        if fetch.exists():
            urls = set(
                re.findall(
                    r'https://www\.3gpp\.org/ftp/Specs/archive/[^"\s]+\.zip',
                    fetch.read_text(encoding="utf-8"),
                )
            )
            missing_urls = sorted(url for url in urls if url not in text)
            if missing_urls:
                add(
                    "03 规范与标准/3GPP/00 3GPP检索索引.md: 下载地址缺 "
                    f"{len(missing_urls)} 条，与 tools/3gpp/fetch.py 的 ITEMS 不一致"
                )


def check_stale(files: list[Path]) -> None:
    for md in files:
        text = md.read_text(encoding="utf-8")
        for match in STALE_SCRIPT_RE.finditer(text):
            add(f"{rel(md)}: 仍引用旧脚本名 {match.group(0)}")
        if ABSOLUTE_RE.search(text):
            add(f"{rel(md)}: 含本机绝对路径，改为相对路径")


def main() -> int:
    files = md_files()
    check_links(files)
    check_tags(files)
    check_basenames(files)
    check_index_counts()
    check_3gpp()
    check_stale(files)

    if problems:
        for problem in problems:
            print(f"FAIL {problem}")
        print(f"\n{len(problems)} 个问题")
        return 1
    print(f"OK: {len(files)} 个 Markdown 文件，链接 / 标签 / 基名 / 索引 / 3GPP 清单全部一致")
    return 0


if __name__ == "__main__":
    sys.exit(main())
