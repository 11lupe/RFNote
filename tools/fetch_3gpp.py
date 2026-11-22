#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""下载并解压 3GPP 规范原文到 ``03 3GPP规范/<规范号>/``。

用法（在仓库根目录执行，任意位置也可）::

    python tools/fetch_3gpp.py                 # 处理 ITEMS 中所有缺失的规范
    python tools/fetch_3gpp.py 38.521-3 25.101 # 只处理指定规范
    python tools/fetch_3gpp.py --list          # 查看清单与本地状态
    python tools/fetch_3gpp.py --no-extract    # 只下载，不解压

约定：
- zip 已存在且大于 1 KB 时跳过下载；`docs/` 已存在时跳过解压。
- 文件名与 3GPP 归档地址一一对应，改规范版本时同时改 ``ITEMS`` 里的 zip 名和 URL。
- 原始包留档不删；`.doc` 转 `.docx` 由 office/LibreOffice 完成，不在本脚本内。
"""
from __future__ import annotations

import argparse
import shutil
import sys
import time
import urllib.request
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "03 3GPP规范"
ARCHIVE = "https://www.3gpp.org/ftp/Specs/archive"

# (规范号, zip 文件名, 下载地址)
ITEMS: list[tuple[str, str, str]] = [
    ("25.101", "25101-j00.zip", f"{ARCHIVE}/25_series/25.101/25101-j00.zip"),
    ("25.133", "25133-j00.zip", f"{ARCHIVE}/25_series/25.133/25133-j00.zip"),
    ("34.108", "34108-f20.zip", f"{ARCHIVE}/34_series/34.108/34108-f20.zip"),
    ("34.121-1", "34121-1-g20.zip", f"{ARCHIVE}/34_series/34.121-1/34121-1-g20.zip"),
    ("36.101", "36101-k10.zip", f"{ARCHIVE}/36_series/36.101/36101-k10.zip"),
    ("36.508", "36508-j31.zip", f"{ARCHIVE}/36_series/36.508/36508-j31.zip"),
    ("36.521-1", "36521-1-j30.zip", f"{ARCHIVE}/36_series/36.521-1/36521-1-j30.zip"),
    ("36.521-2", "36521-2-j30.zip", f"{ARCHIVE}/36_series/36.521-2/36521-2-j30.zip"),
    ("38.101-1", "38101-1-k10.zip", f"{ARCHIVE}/38_series/38.101-1/38101-1-k10.zip"),
    ("38.101-3", "38101-3-k10.zip", f"{ARCHIVE}/38_series/38.101-3/38101-3-k10.zip"),
    ("38.508-1", "38508-1-k00.zip", f"{ARCHIVE}/38_series/38.508-1/38508-1-k00.zip"),
    ("38.521-1", "38521-1-k00.zip", f"{ARCHIVE}/38_series/38.521-1/38521-1-k00.zip"),
    ("38.521-3", "38521-3-k00.zip", f"{ARCHIVE}/38_series/38.521-3/38521-3-k00.zip"),
    ("51.010-1", "51010-1-df0.zip", f"{ARCHIVE}/51_series/51.010-1/51010-1-df0.zip"),
]


def download(url: str, dest: Path) -> None:
    """断点文件先写 ``.part``，完成后原子替换，避免半包被当成完整包。"""
    tmp = dest.parent / (dest.name + ".part")
    req = urllib.request.Request(url, headers={"User-Agent": "RFNote/1.0"})
    started = time.monotonic()
    with urllib.request.urlopen(req, timeout=120) as resp, open(tmp, "wb") as fh:
        total = int(resp.headers.get("Content-Length") or 0)
        got = 0
        while True:
            chunk = resp.read(262144)
            if not chunk:
                break
            fh.write(chunk)
            got += len(chunk)
            if total:
                pct = got * 100 // total
                print(f"\r  {got / 1048576:6.1f}/{total / 1048576:.1f} MB ({pct}%)", end="", flush=True)
    tmp.replace(dest)
    elapsed = max(time.monotonic() - started, 0.01)
    print(f"\r  ok {got / 1048576:.1f} MB in {elapsed:.0f}s ({got / 1048576 / elapsed:.1f} MB/s)")


def extract(zip_path: Path, docs: Path) -> None:
    docs.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path) as zf:
        zf.extractall(docs)
    count = sum(1 for path in docs.rglob("*") if path.is_file())
    print(f"  extracted {count} files")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="下载并解压 3GPP 规范原文")
    parser.add_argument("specs", nargs="*", help="只处理这些规范号（默认全部）")
    parser.add_argument("--list", action="store_true", help="列出清单、下载地址和本地状态，不下载")
    parser.add_argument("--no-extract", action="store_true", help="只下载，不解压")
    parser.add_argument("--root", type=Path, default=ROOT, help="规范库根目录（默认 03 3GPP规范）")
    args = parser.parse_args(argv)

    wanted = set(args.specs)
    unknown = wanted - {spec for spec, _, _ in ITEMS}
    if unknown:
        parser.error(f"未知规范号：{', '.join(sorted(unknown))}")

    for spec, zip_name, url in ITEMS:
        if wanted and spec not in wanted:
            continue
        spec_dir = args.root / spec
        zip_path = spec_dir / zip_name
        exists = zip_path.exists() and zip_path.stat().st_size > 1024
        status = "已下载" if exists else "缺失"
        print(f"[{spec}] {zip_name}  {status}")
        if args.list:
            print(f"  {url}")
            continue

        spec_dir.mkdir(parents=True, exist_ok=True)
        if not exists:
            print(f"  GET {url}")
            try:
                download(url, zip_path)
            except Exception as exc:  # noqa: BLE001 - 网络错误不终止其余规范
                print(f"  DOWNLOAD FAIL: {exc}")
                continue
        else:
            print(f"  exists {zip_path.stat().st_size / 1048576:.1f} MB")

        docs = spec_dir / "docs"
        if args.no_extract:
            continue
        if docs.is_dir() and any(docs.iterdir()):
            print("  docs already present")
            continue
        try:
            extract(zip_path, docs)
        except Exception as exc:  # noqa: BLE001
            print(f"  EXTRACT FAIL: {exc}")

    if args.list:
        selected = [it for it in ITEMS if not wanted or it[0] in wanted]
        missing = [
            spec for spec, zip_name, _ in selected
            if not (args.root / spec / zip_name).is_file()
            or (args.root / spec / zip_name).stat().st_size <= 1024
        ]
        if missing:
            print(f"\n缺失 {len(missing)} 份：{', '.join(missing)}")
            print("运行 python tools/fetch_3gpp.py 下载")
        else:
            print("\n全部已下载")
        return 0

    print("ALL DONE")
    return 0


if __name__ == "__main__":
    sys.exit(main())
