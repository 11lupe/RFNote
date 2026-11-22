# -*- coding: utf-8 -*-
"""为 3GPP 规范（按章节拆分的多个 docx）建立章节索引 CSV。"""
import csv, os, re, sys
from docx import Document

ROOT = r"D:\Project\RFNote\05 3GPP规范"

NUM_RE = re.compile(r"^(\d+(?:\.\d+){0,4})\s+(\S.{0,110})$")
ANNEX_RE = re.compile(r"^(Annex\s+[A-Z][0-9]?)\s*(.{0,100})$")
ANNEX_NUM_RE = re.compile(r"^([A-Z]\.\d+(?:\.\d+){0,3})\s+(\S.{0,110})$")


def is_noise(text):
    t = text.strip()
    if not t:
        return True
    if len(t) > 130:
        return True
    low = t.lower()
    for bad in ("3gpp", "release", "etsi", "ts 3", "ts 5", "©", "copyright",
                "postal address", "office address", "email", "http",
                "route des lucioles", "sophia antipolis", "presented to tsg",
                "or greater indicates", "tsg approved", "change control",
                "the present document", "informative", "void"):
        if bad in low:
            return True
    return False


def clean_title(text):
    """去掉目录行尾的 Tab + 页码。"""
    return re.sub(r"\t+\s*\d+\s*$", "", text).strip()


def scan_docx(path, spec, rows):
    base = os.path.basename(path)
    if "cover" in base.lower():
        return  # 封面/目录文件跳过，避免与正文重复
    try:
        doc = Document(path)
    except Exception as exc:  # noqa
        print(f"  SKIP {base}: {exc}")
        return
    seen = set()
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


def main():
    specs = sorted(d for d in os.listdir(ROOT)
                   if os.path.isdir(os.path.join(ROOT, d)) and re.match(r"^\d\d\.\d{3}", d))
    all_rows = []
    for spec in specs:
        docs = os.path.join(ROOT, spec, "docs")
        if not os.path.isdir(docs):
            print(f"{spec}: no docs dir, skip")
            continue
        docx_files = sorted(f for f in os.listdir(docs) if f.lower().endswith(".docx"))
        doc_files = sorted(f for f in os.listdir(docs) if f.lower().endswith(".doc"))
        rows = []
        for f in docx_files:
            scan_docx(os.path.join(docs, f), spec, rows)
        # 旧格式 .doc 的转换版（docs_docx\）一并扫描
        conv = os.path.join(ROOT, spec, "docs_docx")
        conv_files = []
        if os.path.isdir(conv):
            conv_files = sorted(f for f in os.listdir(conv) if f.lower().endswith(".docx"))
            for f in conv_files:
                scan_docx(os.path.join(conv, f), spec, rows)
        out = os.path.join(ROOT, spec, "章节索引.csv")
        with open(out, "w", encoding="utf-8-sig", newline="") as fh:
            w = csv.writer(fh)
            w.writerow(["规范", "文件", "条款", "标题"])
            w.writerows(rows)
        print(f"{spec}: docx={len(docx_files)} doc={len(doc_files)} conv={len(conv_files)} clauses={len(rows)}")
        all_rows.extend(rows)

    out = os.path.join(ROOT, "检索总表.csv")
    with open(out, "w", encoding="utf-8-sig", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["规范", "文件", "条款", "标题"])
        w.writerows(sorted(all_rows, key=lambda r: (r[0], [int(x) if x.isdigit() else 99 for x in re.findall(r"\d+|[A-Z]", r[2]) or ['99']])))
    print("TOTAL", len(all_rows))


if __name__ == "__main__":
    main()
