"""core.py 的行为规格 —— 这就是你要满足的验收标准。

先跑 `uv run pytest`，全红是正常的。实现一个函数就绿一批，直到全绿。
"""

from __future__ import annotations

from pathlib import Path

from dupefinder.core import (
    file_digest,
    find_duplicates,
    format_report,
    iter_files,
    total_wasted,
)


def make_file(path: Path, content: bytes) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)
    return path


# ---------------------------------------------------------------- iter_files


def test_iter_files_finds_nested_files(tmp_path: Path) -> None:
    make_file(tmp_path / "a.txt", b"a")
    make_file(tmp_path / "sub" / "b.txt", b"b")

    names = {info.path.relative_to(tmp_path).as_posix() for info in iter_files(tmp_path)}

    assert names == {"a.txt", "sub/b.txt"}


def test_iter_files_skips_hidden_entries(tmp_path: Path) -> None:
    make_file(tmp_path / ".git" / "config", b"x")
    make_file(tmp_path / ".hidden", b"x")
    make_file(tmp_path / "visible.txt", b"v")

    names = {info.path.relative_to(tmp_path).as_posix() for info in iter_files(tmp_path)}

    assert names == {"visible.txt"}


def test_iter_files_is_sorted_and_reports_size(tmp_path: Path) -> None:
    make_file(tmp_path / "b.bin", b"12345")
    make_file(tmp_path / "a.bin", b"123")

    infos = list(iter_files(tmp_path))

    assert [info.path.name for info in infos] == ["a.bin", "b.bin"]
    assert [info.size for info in infos] == [3, 5]


# --------------------------------------------------------------- file_digest


def test_digest_same_content_same_hash(tmp_path: Path) -> None:
    a = make_file(tmp_path / "a", b"hello world")
    b = make_file(tmp_path / "b", b"hello world")

    assert file_digest(a) == file_digest(b)


def test_digest_different_content_different_hash(tmp_path: Path) -> None:
    a = make_file(tmp_path / "a", b"hello")
    b = make_file(tmp_path / "b", b"world")

    assert file_digest(a) != file_digest(b)


def test_digest_handles_file_larger_than_chunk(tmp_path: Path) -> None:
    """分块读取的实现必须能处理跨块的文件。"""
    big = make_file(tmp_path / "big", b"x" * 1000)

    assert file_digest(big, chunk_size=7) == file_digest(big)


# ----------------------------------------------------------- find_duplicates


def test_find_duplicates_basic(tmp_path: Path) -> None:
    a = make_file(tmp_path / "a.txt", b"same content")
    b = make_file(tmp_path / "sub" / "b.txt", b"same content")
    make_file(tmp_path / "unique.txt", b"other")

    dups = find_duplicates(tmp_path)

    assert len(dups) == 1
    group = next(iter(dups.values()))
    assert {item.path for item in group} == {a, b}


def test_same_size_different_content_is_not_duplicate(tmp_path: Path) -> None:
    """最容易写错的地方：只看大小会把 abc 和 xyz 判成重复。"""
    make_file(tmp_path / "a", b"abc")
    make_file(tmp_path / "b", b"xyz")

    assert find_duplicates(tmp_path) == {}


def test_find_duplicates_respects_min_size(tmp_path: Path) -> None:
    make_file(tmp_path / "empty1", b"")
    make_file(tmp_path / "empty2", b"")

    assert find_duplicates(tmp_path) == {}
    assert len(find_duplicates(tmp_path, min_size=0)) == 1


def test_find_duplicates_orders_by_wasted_space(tmp_path: Path) -> None:
    for name in ("a", "b"):
        make_file(tmp_path / name, b"x" * 1000)
    for name in ("c", "d", "e"):
        make_file(tmp_path / name, b"y" * 10)

    groups = list(find_duplicates(tmp_path).values())

    assert [group[0].size for group in groups] == [1000, 10]


def test_find_duplicates_group_is_sorted(tmp_path: Path) -> None:
    make_file(tmp_path / "z.txt", b"dup")
    make_file(tmp_path / "a.txt", b"dup")

    group = next(iter(find_duplicates(tmp_path).values()))

    assert [item.path.name for item in group] == ["a.txt", "z.txt"]


def test_find_duplicates_empty_dir(tmp_path: Path) -> None:
    assert find_duplicates(tmp_path) == {}


# ------------------------------------------------------------ total_wasted


def test_total_wasted(tmp_path: Path) -> None:
    for name in ("a", "b", "c"):
        make_file(tmp_path / name, b"x" * 100)

    dups = find_duplicates(tmp_path)

    assert total_wasted(dups) == 200


def test_total_wasted_empty() -> None:
    assert total_wasted({}) == 0


# ------------------------------------------------------------ format_report


def test_format_report_lists_files_and_total(tmp_path: Path) -> None:
    make_file(tmp_path / "a.txt", b"dup content")
    make_file(tmp_path / "sub" / "b.txt", b"dup content")

    text = format_report(find_duplicates(tmp_path), tmp_path)

    assert "a.txt" in text
    assert "sub" in text
    assert "可回收" in text


def test_format_report_when_no_duplicates(tmp_path: Path) -> None:
    assert format_report({}, tmp_path) == "没有发现重复文件"


def test_iter_files_excludes_directories(tmp_path: Path) -> None:
    make_file(tmp_path / "keep.txt", b"a")
    make_file(tmp_path / "node_modules" / "dep.txt", b"a")

    names = {i.path.name for i in iter_files(tmp_path, exclude={"node_modules"})}

    assert names == {"keep.txt"}


def test_find_duplicates_with_exclude(tmp_path: Path) -> None:
    make_file(tmp_path / "a.txt", b"same")
    make_file(tmp_path / "b.txt", b"same")
    make_file(tmp_path / "cache" / "c.txt", b"same")

    dups = find_duplicates(tmp_path, exclude={"cache"})

    assert len(dups) == 1
    assert len(next(iter(dups.values()))) == 2  # 只剩 a、b 两个
