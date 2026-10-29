"""命令行入口：只负责参数解析和输出，业务逻辑都在 core.py。

这一层刻意写得很薄——面试时"分层"不是口号，CLI/HTTP 都是同一套业务逻辑的外壳。
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Annotated

import typer

from dupefinder.core import find_duplicates, format_report

app = typer.Typer(
    help="查找目录下的重复文件（按内容比对，不是按文件名）",
    no_args_is_help=True,
    add_completion=False,
)

RootArg = Annotated[
    Path,
    typer.Argument(
        exists=True,
        file_okay=False,
        dir_okay=True,
        resolve_path=True,
        help="要扫描的目录",
    ),
]
MinSizeOpt = Annotated[
    int,
    typer.Option("--min-size", min=0, help="只统计不小于该字节数的文件（默认 1，忽略空文件）"),
]
JsonOpt = Annotated[bool, typer.Option("--json", help="输出 JSON，方便交给脚本处理")]
ExcludeOpt = Annotated[
    list[str] | None,
    typer.Option("--exclude", "-e", help="要跳过的目录名，可重复指定"),
]


@app.callback()
def main() -> None:
    """重复文件查找工具：按内容比对，不按文件名。"""
    # 没有这个 callback，Typer 会把唯一的子命令提升成顶层命令，`dupe find .` 就会变成 `dupe .`


@app.command()
def find(
    root: RootArg = Path("."),
    min_size: MinSizeOpt = 1,
    as_json: JsonOpt = False,
    exclude: ExcludeOpt = None,
) -> None:
    """扫描目录并列出重复文件。"""
    dups = find_duplicates(root, min_size=min_size, exclude=exclude or ())

    if as_json:
        payload = [
            {
                "hash": digest,
                "size": group[0].size,
                "wasted": group[0].size * (len(group) - 1),
                "files": [str(item.path) for item in group],
            }
            for digest, group in dups.items()
        ]
        typer.echo(json.dumps(payload, ensure_ascii=False, indent=2))
        return

    typer.echo(format_report(dups, root))


if __name__ == "__main__":  # 方便 python -m dupefinder.cli 调试
    app()
