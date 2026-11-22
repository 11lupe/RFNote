# 仓库工具

三个只依赖标准库的脚本（`index_3gpp.py` 另需 `python-docx`），都在仓库根目录执行，
路径从脚本位置推导，不写死本机目录。

| 脚本 | 作用 | 常用命令 |
| --- | --- | --- |
| `fetch_3gpp.py` | 按 `ITEMS` 清单下载 / 解压 3GPP 原文 | `python tools/fetch_3gpp.py --list` |
| `index_3gpp.py` | 重建 `章节索引.csv` 与 `检索总表.csv` | `python tools/index_3gpp.py --check` |
| `check_repo.py` | 链接、标签、基名、索引计数、规范库一致性自检 | `python tools/check_repo.py` |

## 日常

```bash
# 提交前自检（CI 也跑这一条）
python tools/check_repo.py

# 新增/更新规范后重建索引
python tools/index_3gpp.py

# 只下载缺失的规范，或指定几份
python tools/fetch_3gpp.py
python tools/fetch_3gpp.py 38.521-3 25.101
```

`index_3gpp.py` 需要 `python-docx`；`fetch_3gpp.py` 需要能访问 `www.3gpp.org`。
`.doc` 转 `.docx` 用 LibreOffice / Office 完成，不在脚本内。
