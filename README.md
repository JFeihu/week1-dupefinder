# W1 练手：重复文件查找器（dupefinder）

一个真正能用的小工具：扫描目录，找出**内容相同**的文件，报告能省多少空间。

这个项目不是让你「抄一遍」，而是让你在真实场景里把 W1 的工具链用熟：

- `uv` 管依赖和环境（不再手敲 `venv` + `pip`）
- `pytest` 写测试、跑测试
- `ruff` 检查风格和常见 bug
- `pre-commit` 在提交前自动跑检查
- `git` 提交、推送

## 现在的状态

`tests/` 里已经写好了 **18 个测试**，全部是红的——因为 `src/dupefinder/core.py` 里只有函数签名和 docstring。
**你的任务：把 4 个函数实现出来，让测试全绿。**

先用 30 秒理解结构：

```text
src/dupefinder/core.py   ← 你要实现的业务逻辑（唯一要改的文件）
src/dupefinder/cli.py    ← 已经写好，演示「CLI 只是薄薄一层壳」
tests/test_core.py       ← 行为规格，读它就知道每个函数要干什么
tests/test_cli.py        ← 端到端：命令行能不能跑通
```

## 开始

```powershell
cd E:\deepseek\workspace\week1-dupefinder
uv sync                     # 建 .venv 并装依赖（含 dev 组）
uv run pytest               # 你会看到 18 个 failed，正常
```

然后打开 `src/dupefinder/core.py`，**从 `iter_files` 开始**，实现一个就跑一次 `uv run pytest`，看着红的变绿。

## 完成标准（四个都必须做到）

1. `uv run pytest` **全绿**，且不修改 `tests/` 里已有的断言；
2. 自己**补 7 个以上**边界用例（下面给了清单），总数 ≥ 25；
3. `uv run ruff check .` 和 `uv run ruff format --check .` 都通过；
4. `pre-commit install` 之后提交，钩子能通过；推到 GitHub 新仓库 `week1-dupefinder`。

### 建议补的边界用例（挑 7 个）

- 空目录 / 只有一个文件
- 三个及以上文件内容相同
- 大小相同、内容不同（**最重要**，防止只看 size 的写法）
- 0 字节文件（默认 min_size=1 应被忽略）
- 文件名带中文 / 空格
- 深层嵌套目录
- `.git`、`.venv` 这类隐藏目录被跳过
- 大的二进制文件（构造 2MB 内容，验证分块读取没写错）
- `format_report` 的输出里相对路径是否正常

## 命令速查

```powershell
uv run pytest -v                    # 看每个用例名字
uv run pytest tests/test_core.py::test_find_duplicates_basic
uv run pytest --cov=dupefinder      # 覆盖率
uv run ruff check . --fix           # 自动修能修的
uv run ruff format .
uv run dupe find .                  # 用你的工具扫自己（很好玩）
uv run dupe find . --json
pre-commit install                  # 之后每次 git commit 自动检查
```

## 卡住了再看（实现提示）

<details>
<summary>点开：四个函数的思路提示</summary>

**iter_files**

- `Path.rglob("*")` 递归列出所有条目；用 `p.is_file()` 判断普通文件。
- 跳过隐藏：`p.relative_to(root).parts` 里任何一段以 `.` 开头就跳过；`.venv` 会被一起跳过。
- 跳过符号链接：`p.is_symlink()`。
- 排序：`sorted(files, key=lambda i: str(i.path))`。

**file_digest**

- `hashlib.sha256()`，分块读：`for chunk in iter(lambda: f.read(chunk_size), b"")`——这个 `iter(callable, sentinel)` 写法是标准技巧，值得记住。
- 记得 `return hasher.hexdigest()`。

**find_duplicates**

- 先用 `defaultdict(list)` 按 `size` 分桶，只有桶里 ≥2 个文件才值得算哈希。
- 桶内再按哈希分组，保留 `len >= 2` 的组。
- 组内排序 + 整体按「浪费空间」倒序：`size * (len(group) - 1)`。

**format_report**

- 相对路径：`item.path.relative_to(root)`。
- 人眼友好的大小：写个 `_human_size(n)`，按 1024 进位到 KB/MB。
- 空结果直接 `return "没有发现重复文件"`（测试要求完全相等）。

</details>

## 提交

```powershell
git init
git add .
git commit -m "feat: 实现重复文件查找 CLI"
# 在 GitHub 新建空仓库 week1-dupefinder 后：
git remote add origin git@github.com:<你的用户名>/week1-dupefinder.git
git push -u origin main
```

> 记得 `<你的用户名>` 是占位符，**连尖括号一起替换**。

## 做完之后

在 README 顶部加三行：这个工具解决什么问题、怎么用、跑一次的真实输出（比如扫描你的下载目录省了多少 MB）。
这三行以后就是简历上「项目经历」的素材。
