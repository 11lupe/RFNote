#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把仪表官方文档（PDF）下载到 ``04 仪表与设备/厂商文档/<仪表>/``。

文档随笔记一起入库，文件名保持厂商原文（带版本号）；各篇仪表笔记的
「官方文档与命令参考」一节用相对路径链到这些 PDF。

用法（在仓库根目录执行）::

    python tools/instruments/fetch.py                  # 下载缺失的全部文档
    python tools/instruments/fetch.py fsw-manual 1cm95 # 只处理指定几份
    python tools/instruments/fetch.py --list           # 清单、地址、本地状态
    python tools/instruments/fetch.py --dir D:/doc     # 换下载根目录

约定：
- 本地文件大于 1 KB 视为已下载；先写 ``.part`` 再原子替换，半包不会被当成完整包。
- 地址随厂商版本滚动，``DOCS`` 里的文件名带版本号（en_57、1CM95_v1…），
  404 时先去厂商页面确认新版本，再同时改笔记里的链接与本清单。
- 新增文档时先建好 ``04 仪表与设备/厂商文档/<仪表>/``，再在 ``DOCS`` 里登记 subdir。
"""
from __future__ import annotations

import argparse
import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2] / "04 仪表与设备" / "厂商文档"
RS = "https://scdn.rohde-schwarz.com/ur/pws/dl_downloads"

# (键, 子目录, 厂商, 标题, 本地文件名, 下载地址, 约 MB)
DOCS: list[tuple[str, str, str, str, str, str, float]] = [
    (
        "fsw-manual", "FSW", "FSW", "FSW User Manual en_57（1173.9411.01）",
        "FSW_UserManual_en_57.pdf",
        f"{RS}/pdm/cl_manuals/user_manual/1173_9411_01/FSW_UserManual_en_57.pdf", 32.1,
    ),
    (
        "fsw-getting-started", "FSW", "FSW", "FSW Getting Started en_17（1338.4102.01）",
        "FSW_GettingStarted_en_17.pdf",
        f"{RS}/pdm/cl_manuals/getting_started/1338_4102_01/FSW_GettingStarted_en_17.pdf", 13.5,
    ),
    (
        "fsw-k144", "FSW", "FSW", "FSW-K144 5G NR 下行测量手册 en_18（1178.8036.01）",
        "FSW_K144_5G_NR_DL_UserManual_en_18~2.pdf",
        f"{RS}/pdm/cl_manuals/user_manual/1178_8036_01/FSW_K144_5G_NR_DL_UserManual_en_18~2.pdf", 5.6,
    ),
    (
        "fsw-k145", "FSW", "FSW", "FSW-K145 5G NR 上行测量手册 en_17（1178.8042.01）",
        "FSW_K145_5G_NR_UL_UserManual_en_17~1.pdf",
        f"{RS}/pdm/cl_manuals/user_manual/1178_8042_01/FSW_K145_5G_NR_UL_UserManual_en_17~1.pdf", 5.2,
    ),
    (
        "1cm95", "CMW500", "CMW500", "1CM95 WCDMA RF 测量（按 TS 34.121）",
        "1CM95_v1.pdf",
        f"{RS}/dl_application/application_notes/1cm95/1CM95_v1.pdf", 2.4,
    ),
    (
        "1cm97", "CMW500", "CMW500", "1CM97 HSUPA RF 测量（按 TS 34.121）",
        "1CM97_v01_HSUPA_CMW.pdf",
        f"{RS}/dl_application/application_notes/1cm97/1CM97_v01_HSUPA_CMW.pdf", 2.1,
    ),
    (
        "1cm94", "CMW500", "CMW500", "1CM94 LTE UE RF 测量（按 TS 36.521-1）",
        "1CM94_5e_LTE_UE_RF_Meas_TS36121-1.pdf",
        f"{RS}/dl_application/application_notes/1cm94/1CM94_5e_LTE_UE_RF_Meas_TS36121-1.pdf", 3.7,
    ),
    (
        "1cm103", "CMW500", "CMW500", "1CM103 CMW500 测量 LTE 终端下行载波聚合（中文）",
        "1CM_103_1c.pdf",
        f"{RS}/dl_application/application_notes/1cm103/1CM_103_1c.pdf", 1.4,
    ),
    (
        "1ma166", "CMW500", "CMW500", "1MA166 LTE-Advanced Rel-10 测试（CA 原理与验证）",
        "1MA166_5e_LTE_Rel10_Testing.pdf",
        f"{RS}/dl_application/application_notes/1ma166/1MA166_5e_LTE_Rel10_Testing.pdf", 45.1,
    ),
    (
        "1ma272", "CMW500", "CMW500", "1MA272 LTE Rel-11/12 测试",
        "1MA272_2e_Testing_LTE_Rel_11_12.pdf",
        f"{RS}/dl_application/application_notes/1ma272/1MA272_2e_Testing_LTE_Rel_11_12.pdf", 4.9,
    ),
    (
        "1ma121", "CMW500", "CMW500", "1MA121 HSUPA/HSPA+ 测试",
        "1MA121_Testing_HSPA_5e.pdf",
        f"{RS}/dl_application/application_notes/1ma121/1MA121_Testing_HSPA_5e.pdf", 5.2,
    ),
    (
        "1ma231", "通用", "通用", "1MA231 移动无线电测量总览（GSM/WCDMA/LTE 原理）",
        "1MA231_3e_Mobile_Radio_Meas.pdf",
        f"{RS}/dl_application/application_notes/1ma231/1MA231_3e_Mobile_Radio_Meas.pdf", 4.3,
    ),
    (
        "gfm322", "通用", "通用", "GFM322 5G NR 信号生成与分析",
        "GFM322_1e_5GNR_gen_analysis.pdf",
        f"{RS}/dl_application/application_notes/gfm322/GFM322_1e_5GNR_gen_analysis.pdf", 8.4,
    ),
]


def download(url: str, dest: Path) -> int:
    tmp = dest.parent / (dest.name + ".part")
    req = urllib.request.Request(url, headers={"User-Agent": "RFNote/1.0"})
    started = time.monotonic()
    got = 0
    with urllib.request.urlopen(req, timeout=180) as resp, open(tmp, "wb") as fh:
        total = int(resp.headers.get("Content-Length") or 0)
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
    print(f"\r  ok {got / 1048576:.1f} MB in {elapsed:.0f}s ({got / 1048576 / elapsed:.1f} MB/s)   ")
    return got


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="下载仪表官方文档 PDF 到 04 仪表与设备/厂商文档")
    parser.add_argument("keys", nargs="*", help="只处理这些键（默认全部）")
    parser.add_argument("--list", action="store_true", help="列出清单、下载地址与本地状态，不下载")
    parser.add_argument("--dir", type=Path, default=ROOT, help=f"下载根目录（默认 {ROOT}）")
    args = parser.parse_args(argv)

    wanted = set(args.keys)
    unknown = wanted - {key for key, *_ in DOCS}
    if unknown:
        parser.error(f"未知键：{', '.join(sorted(unknown))}；用 --list 查看")

    selected = [item for item in DOCS if not wanted or item[0] in wanted]
    missing = 0
    for key, subdir, vendor, title, name, url, size_mb in selected:
        dest = args.dir / subdir / name
        exists = dest.is_file() and dest.stat().st_size > 1024
        print(f"[{key}] {vendor} · {title}")
        if args.list:
            print(f"  {url}")
            print(f"  {'已下载' if exists else '缺失'} {dest}（约 {size_mb:.1f} MB）")
            missing += 0 if exists else 1
            continue
        if exists:
            print(f"  exists {dest.stat().st_size / 1048576:.1f} MB")
            continue
        dest.parent.mkdir(parents=True, exist_ok=True)
        print(f"  GET {url}")
        try:
            download(url, dest)
        except Exception as exc:  # noqa: BLE001 - 网络错误不终止其余文档
            missing += 1
            print(f"  DOWNLOAD FAIL: {exc}")

    if args.list and missing:
        print(f"\n缺失 {missing} 份；运行 python tools/instruments/fetch.py 下载")
    return 0


if __name__ == "__main__":
    sys.exit(main())
