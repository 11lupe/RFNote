# 仓库工具

脚本按用途分目录，避免后续数量变多时不好区分。新脚本先归入已有类目；
确实需要新类目时，在本文件登记后再加目录。

```
tools/
├── 3gpp/              # 3GPP 数据维护
│   ├── fetch.py       # 下载 / 解压规范原文
│   └── index.py       # 重建章节索引与检索总表
├── instruments/       # 仪表官方文档（厂商 PDF，不入库）
│   └── fetch.py       # 下载手册到 _local/仪表文档/
└── repo/              # 仓库级自检
    └── check.py       # 链接 / 标签 / 索引 / 规范库一致性
```

| 目录 | 脚本 | 作用 | 常用命令 |
| --- | --- | --- | --- |
| `3gpp/` | `fetch.py` | 按 `ITEMS` 清单下载 / 解压 3GPP 原文 | `python tools/3gpp/fetch.py --list` |
| `3gpp/` | `index.py` | 重建 `章节索引.csv` 与 `检索总表.csv` | `python tools/3gpp/index.py --check` |
| `instruments/` | `fetch.py` | 把仪表手册 PDF 下载到 `04 仪表与设备/厂商文档/` | `python tools/instruments/fetch.py --list` |
| `repo/` | `check.py` | 链接、标签、基名、索引计数、规范库一致性自检 | `python tools/repo/check.py` |

三个脚本都只依赖标准库（`index.py` 另需 `python-docx`），都在仓库根目录执行，
路径从脚本位置推导，不写死本机目录。

## 日常

```bash
# 提交前自检（CI 也跑这一条）
python tools/repo/check.py

# 新增/更新规范后重建索引
python tools/3gpp/index.py

# 只下载缺失的规范，或指定几份
python tools/3gpp/fetch.py
python tools/3gpp/fetch.py 38.521-3 25.101
```

`index.py` 需要 `python-docx`；`fetch.py` 需要能访问 `www.3gpp.org`。
原始 zip 不入库（`.gitignore` 已排除 `03 规范与标准/3GPP/*/*.zip`），下载后留在本地即可；
`docs/` 里的 docx 是转换成果，随仓库跟踪。
`.doc` 转 `.docx` 用 LibreOffice / Office 完成，不在脚本内。
