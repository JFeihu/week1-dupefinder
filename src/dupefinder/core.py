"""重复文件查找：核心逻辑（你要实现的就是这个文件）。

规则：先按文件大小分桶，大小唯一的文件直接排除；只对"大小相同的候选"计算哈希。
这样能避免对每个文件都做全量哈希，扫描 10 万文件时差别非常明显。
"""

from __future__ import annotations

import hashlib
from collections import defaultdict
from collections.abc import Collection, Iterator
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class FileInfo:
    path: Path
    size: int


def iter_files(root: Path, exclude: Collection[str] = ()) -> Iterator[FileInfo]:
    """递归遍历 root 下的所有普通文件。

    要求：
    - 跳过隐藏文件/隐藏目录（名字以 . 开头，例如 .git、.venv）；
    - 跳过符号链接（避免循环）；
    - 跳过不是普通文件的条目（目录、管道等）；
    - 结果按路径字符串升序返回，保证同样的目录结构每次输出一致。

    Yields:
        FileInfo，其中 size 是文件字节数。
    """
    # 收集、排序、使用正斜杠的路径字符串
    files = []
    # .rglob("*") ==> 递归的遍历路径下的文件和文件夹
    for p in root.rglob("*"):
        # print(p.parts)
        # 跳过符号链接和非普通文件
        if p.is_symlink() or not p.is_file():
            continue
        # 跳过隐藏文件/文件夹   相对 root 判断隐藏（不是 p.parts，那是绝对路径的所有层级）
        if any(part.startswith(".") for part in p.relative_to(root).parts):
            continue
        rel_part = p.relative_to(root).parts
        if any(part in exclude for part in rel_part):  # 路径里任何一段命中就跳过
            continue
        # 只保留普通文件
        files.append(FileInfo(path=p, size=p.stat().st_size))
    # 排序
    files.sort(key=lambda info: str(info.path))
    yield from files


def file_digest(path: Path, chunk_size: int = 1 << 20) -> str:
    """计算文件的 sha256 十六进制摘要。

    要求：必须分块读取（默认每块 1 MiB），不能把整个文件读进内存。
    """
    hasher = hashlib.sha256()
    with path.open("rb") as fh:
        while chunk := fh.read(chunk_size):
            hasher.update(chunk)
        return hasher.hexdigest()


def find_duplicates(
    root: Path, min_size: int = 1, exclude: Collection[str] = ()
) -> dict[str, list[FileInfo]]:
    """找出 root 下内容完全相同的文件，按「哈希 → 文件列表」返回。

    要求：
    - 只统计大小 >= min_size 的文件（默认 1 字节，即忽略空文件）；
    - 大小相同但内容不同的文件**不能**被当成重复（所以不能只比大小）；
    - 只返回出现 2 次及以上的组；
    - 每组内部按路径字符串升序排列；
    - 返回的字典按「可回收空间的多少」从大到小排列（大组在前）；
    - 没有重复时返回空字典 {}。
    """
    by_size: dict[int, list[FileInfo]] = defaultdict(list)
    for info in iter_files(root, exclude=exclude):
        if info.size >= min_size:
            by_size[info.size].append(info)

    result: dict[str, list[FileInfo]] = {}

    for candidates in by_size.values():
        if len(candidates) < 2:
            continue  # 文件大小位唯一的，直接跳过

        # 桶内按 hash 分组
        by_hash = defaultdict(list)
        for info in candidates:
            by_hash[file_digest(info.path)].append(info)

        # 只保留重复组，组内按路径排序
        for digest, group in by_hash.items():
            if len(group) >= 2:
                result[digest] = sorted(group, key=lambda i: str(i.path))

    # 组间按“浪费空间”倒序
    return dict(
        sorted(
            result.items(),
            key=lambda kv: kv[1][0].size * (len(kv[1]) - 1),
            reverse=True,
        )
    )


def total_wasted(dups: dict[str, list[FileInfo]]) -> int:
    """可回收的字节数：每组保留 1 份，其余 (n-1) 份都是浪费。"""
    return sum(group[0].size * (len(group) - 1) for group in dups.values())


def format_report(dups: dict[str, list[FileInfo]], root: Path) -> str:
    """生成给人看的报告文本。

    要求：
    - 每组一个标题，包含序号和该组文件个数；
    - 每个文件一行，路径显示为相对 root 的相对路径；
    - 末尾有一行汇总，包含「可回收」和总字节数；
    - dups 为空时返回 "没有发现重复文件"。
    """
    if not dups:
        return "没有发现重复文件"

    lines = [f"发现 {len(dups)} 组重复文件：", ""]
    for index, group in enumerate(dups.values(), start=1):
        lines.append(f"【{index}】{len(group)} 个文件，每个 {group[0].size} 字节")
        for item in group:
            lines.append(f"  - {item.path.relative_to(root).as_posix()}")
        lines.append("")
    lines.append(f"合计可回收：{total_wasted(dups)} 字节")
    return "\n".join(lines)
