# -*- coding: utf-8 -*-
"""下载并解压 3GPP 规范到 05 3GPP规范\<spec>\ 。"""
import os
import shutil
import sys
import time
import urllib.request
import zipfile

ROOT = r"D:\Project\RFNote\05 3GPP规范"
OLD = r"D:\Project\RFNote\05 3GPP规范\_old_zips"

A = "https://www.3gpp.org/ftp/Specs/archive"

ITEMS = [
    ("36.101",   "36101-k10.zip",   "old"),
    ("36.508",   "36508-j31.zip",   f"{A}/36_series/36.508/36508-j31.zip"),
    ("36.521-1", "36521-1-j30.zip", "old"),
    ("36.521-2", "36521-2-j30.zip", f"{A}/36_series/36.521-2/36521-2-j30.zip"),
    ("38.101-1", "38101-1-k10.zip", "old"),
    ("38.101-3", "38101-3-k10.zip", f"{A}/38_series/38.101-3/38101-3-k10.zip"),
    ("38.508-1", "38508-1-k00.zip", f"{A}/38_series/38.508-1/38508-1-k00.zip"),
    ("38.521-1", "38521-1-k00.zip", "old"),
    ("38.521-3", "38521-3-k00.zip", f"{A}/38_series/38.521-3/38521-3-k00.zip"),
    ("51.010-1", "51010-1-df0.zip", "old"),
    # WCDMA / UMTS
    ("25.101",   "25101-j00.zip",   f"{A}/25_series/25.101/25101-j00.zip"),
    ("25.133",   "25133-j00.zip",   f"{A}/25_series/25.133/25133-j00.zip"),
    ("34.108",   "34108-f20.zip",   f"{A}/34_series/34.108/34108-f20.zip"),
    ("34.121-1", "34121-1-g20.zip", f"{A}/34_series/34.121-1/34121-1-g20.zip"),
]


def download(url, dest):
    tmp = dest + ".part"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    t0 = time.time()
    with urllib.request.urlopen(req, timeout=120) as r, open(tmp, "wb") as fh:
        total = int(r.headers.get("Content-Length") or 0)
        got = 0
        while True:
            chunk = r.read(262144)
            if not chunk:
                break
            fh.write(chunk)
            got += len(chunk)
    os.replace(tmp, dest)
    dt = max(time.time() - t0, 0.01)
    print(f"  ok {got/1048576:.1f} MB in {dt:.0f}s ({got/1048576/dt:.1f} MB/s)")


def main():
    for spec, zipname, src in ITEMS:
        d = os.path.join(ROOT, spec)
        os.makedirs(d, exist_ok=True)
        zp = os.path.join(d, zipname)
        print(f"[{spec}] {zipname}", flush=True)
        if not os.path.exists(zp) or os.path.getsize(zp) < 1024:
            if src == "old":
                shutil.copy2(os.path.join(OLD, zipname), zp)
                print("  copied from _old_zips")
            else:
                try:
                    download(src, zp)
                except Exception as exc:
                    print(f"  DOWNLOAD FAIL: {exc}")
                    continue
        else:
            print(f"  exists {os.path.getsize(zp)/1048576:.1f} MB")

        docs = os.path.join(d, "docs")
        if not os.path.isdir(docs):
            try:
                with zipfile.ZipFile(zp) as z:
                    z.extractall(docs)
                n = sum(len(f) for _, _, f in os.walk(docs))
                print(f"  extracted {n} files")
            except Exception as exc:
                print(f"  EXTRACT FAIL: {exc}")
        else:
            print("  docs already present")
    print("ALL DONE", flush=True)


if __name__ == "__main__":
    main()
