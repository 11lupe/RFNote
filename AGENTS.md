# AGENTS.md

射频知识库（RFNote）的 Agent 指南。**动手前先读本文件**；约定与目录说明见 [README.md](README.md) 与 [00 标签与命名规范.md](<00 标签与命名规范.md>)。

## 这是什么

面向手机射频自动化测试开发的学习库：7 篇主题笔记 + 4 个域索引 + 3GPP 规范原文检索库（14 份规范，约 460 MB）。2026-11 从 `SomeNote/工作/射频` 迁出独立成库。

## 目录地图

```
RFNote/
├── README.md                  # 总入口：目录表、阅读路径、当前进度
├── 00 标签与命名规范.md        # 目录/标签/链接/敏感信息约定
├── 01 基础概念/                # 概念仓库（单文件追加制）
├── 02 测试指标/                # A 类指标深挖 + Dxx 课程讲义
├── 03 学习路径/                # 分级地图、4 周方案、进度看板
├── 04 面试/                    # 回答口径、追问链、反问清单
└── 05 3GPP规范/                # 规范原文 + 检索索引 + 生成脚本
    ├── 00 3GPP检索索引.md
    ├── 检索总表.csv
    ├── _fetch.py / _index.py
    └── <规范号>/  zip + docs/ + docs_docx/ + 章节索引.csv
```

## 硬规则

1. **知识文档只放知识**。面试话术只进 `04 面试`；进度、复习队列只进 `03 学习路径/射频学习_进度看板.md`；不跨文件复制同一正文。
2. **一篇一主题**，文件名不含空格（顶层目录可含）。学习课程序列用 `Dxx ` 前缀，放 `02 测试指标/`。
3. **链接必须相对路径 + 尖括号**：`[文本](<02 测试指标/D01 最大功率与MPR.md>)`；路径含空格时缺了尖括号 GitHub 会渲染断。基名全库唯一，改名要全库同步引用。
4. **限值数字只作量级参考**，判定以 3GPP 原文表格 + 平台/客户配置为准；引用限值必须标规范号与节号。
5. **不写真实敏感信息**：内网地址、账号、客户名、测试机名一律 `<占位符>`。
6. **3GPP 原始包（`*.zip`）留档不删**；`docs/` 里的 docx 是转换成果，不要手改，改章节内容走重新转换 + 重建索引。
7. 提交前跑一遍链接校验（见下），不提交死链。

## 常见任务

**新增一课**
1. 在 `02 测试指标/` 建 `Dxx 主题.md`，加 frontmatter（`域/测试指标` + `类型/...` + `状态/待补`）。
2. `02 测试指标/00 测试指标索引.md` 课程表补一行；`03 学习路径/射频学习_进度看板.md` 更新状态与「下次继续」。

**新增/更新规范**
1. `05 3GPP规范/_fetch.py` 的 `ITEMS` 加条目（或改 URL/解压步骤），运行下载。
2. 转换 docx 后运行 `_index.py` 重建 `检索总表.csv` 与各 `章节索引.csv`。
3. `05 3GPP规范/00 3GPP检索索引.md` 补规范清单、目录树与「指标 → 条款定位表」。

**重建索引**（需 python-docx）
```bash
cd "D:/Project/RFNote/05 3GPP规范"
python _index.py            # 重新扫描 docs_docx，生成检索总表与章节索引
python _fetch.py            # 按 ITEMS 下载缺失规范（可选）
```

## 校验

```bash
# 1) 相对链接可解析：列出所有 markdown 链接目标并逐个 test -f
python - <<'PY'
import re, pathlib, urllib.parse
root = pathlib.Path("D:/Project/RFNote")
bad = []
for md in root.rglob("*.md"):
    for m in re.finditer(r"\]\((<[^>]+>|[^)\s]+)\)", md.read_text(encoding="utf-8")):
        t = m.group(1).strip("<>")
        if t.startswith(("http", "#", "mailto:")): continue
        p = (md.parent / urllib.parse.unquote(t.split("#")[0])).resolve()
        if not p.exists(): bad.append(f"{md.relative_to(root)} -> {t}")
print("\n".join(bad) or "links OK")
PY

# 2) 基名唯一 + 文件计数
git ls-files | sort | uniq -d
```

## 备注

- 仓库约 460 MB（规范原文为主），**不要**为了瘦身删 zip 或 docx；需要轻量克隆时用 README 里的 sparse-checkout。
- 当前进度以 `03 学习路径/射频学习_进度看板.md` 为准，README 的「当前进度」是它的摘要，改进度两边同步。
