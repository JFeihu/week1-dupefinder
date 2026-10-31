# dupefinder

扫描目录，找出内容相同的文件，告诉你浪费了多少空间。

<!-- TODO（给自己看，渲染时不显示）：补一句更具体的真实场景，比如"我的下载目录里同一份安装包下了 3 次" -->

## 为什么做这个

日常文件重复下载容易占用大量存储空间，市面上同类工具大多收费，或者在 Windows 下路径兼容不佳。
这个工具就是为了解决这些痛点：按**内容**比对，跨平台可用，一条命令给出可回收的空间。

## 安装

```powershell
uv sync
```

## 用法

```powershell
uv run dupe find .                                    # 扫描当前目录
uv run dupe find D:\Downloads --min-size 1024         # 只算大于 1KB 的
uv run dupe find . --exclude node_modules -e .venv    # 跳过指定目录
uv run dupe find . --json                             # 交给脚本处理
uv run dupe version
```

## 输出示例

```text
$ uv run dupe find D:\Downloads

发现 2 组重复文件：

【1】3 个文件，每个 1048576 字节
  - install/setup.exe
  - install/setup (1).exe
  - backup/setup.exe

【2】2 个文件，每个 2048 字节
  - note.txt
  - note - 副本.txt

合计可回收：2101248 字节
```

## 它是怎么工作的

1. 递归扫描，跳过隐藏目录和你指定的目录
2. 先按文件大小分组——大小不同，内容一定不同
3. 只对大小相同的候选算 SHA-256
4. 按指纹分组，得到重复文件组

## 项目结构

```text
src/dupefinder/
├── core.py    业务逻辑：扫描、哈希、分组、报告（纯函数，不打印）
└── cli.py     命令行层：参数解析 + 输出（薄壳）
```

## 技术点

- **大小分桶**：避免对每个文件都做全量哈希，10 万文件里大部分大小唯一
- **分块读取（1 MiB）**：1GB 的文件也不吃内存
- **生成器**：边遍历边处理，不用先攒一个大列表
- **`dataclass(frozen=True, slots=True)`**：轻量不可变对象，几万个实例也省内存

## 开发

```powershell
uv run pytest -q
uv run ruff check .
uv run mypy src
uv run pre-commit run --all-files
```

## 局限

- 只按内容比对，不识别硬链接（同一份数据的两种路径会被当成两个文件）
- 扫描大目录时速度受磁盘 IO 限制
- 不做跨盘符去重
