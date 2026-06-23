"""
测试 Asset Sweeper 的核心功能
"""

import pytest
from pathlib import Path
from aegis.engines.sweeper import AssetSweeper, ScanResult


@pytest.fixture
def temp_project(tmp_path):
    """创建临时测试项目"""
    # 创建目录结构
    (tmp_path / "src").mkdir()
    (tmp_path / "node_modules").mkdir()
    (tmp_path / "__pycache__").mkdir()
    (tmp_path / "dist").mkdir()

    # 创建文件
    (tmp_path / "src" / "main.py").write_text("print('hello')")
    (tmp_path / "src" / "test.pyc").write_text("compiled")
    (tmp_path / "node_modules" / "package.json").write_text("{}")
    (tmp_path / "__pycache__" / "cache.pyc").write_text("cache")

    return tmp_path


def test_should_ignore_dir():
    """测试目录忽略规则"""
    sweeper = AssetSweeper(
        ignore_dirs=["node_modules", "__pycache__"],
        ignore_extensions=[".pyc"]
    )

    assert sweeper.should_ignore_dir(Path("node_modules"))
    assert sweeper.should_ignore_dir(Path("__pycache__"))
    assert not sweeper.should_ignore_dir(Path("src"))


def test_should_ignore_file():
    """测试文件忽略规则"""
    sweeper = AssetSweeper(
        ignore_dirs=[],
        ignore_extensions=[".pyc", ".pyo"]
    )

    assert sweeper.should_ignore_file(Path("test.pyc"))
    assert sweeper.should_ignore_file(Path("test.pyo"))
    assert not sweeper.should_ignore_file(Path("test.py"))


def test_scan_directory(temp_project):
    """测试目录扫描"""
    sweeper = AssetSweeper(
        ignore_dirs=["node_modules", "__pycache__", "dist"],
        ignore_extensions=[".pyc"]
    )

    result = sweeper.scan_directory(temp_project)

    # 验证扫描结果
    assert result.total_files > 0
    assert len(result.ignorable_dirs) >= 2  # node_modules, __pycache__
    assert len(result.ignorable_files) >= 1  # src/test.pyc


@pytest.mark.asyncio
async def test_scan_async(temp_project):
    """测试异步扫描"""
    sweeper = AssetSweeper(
        ignore_dirs=["node_modules", "__pycache__"],
        ignore_extensions=[".pyc"]
    )

    result = await sweeper.scan_async(temp_project)

    assert result.total_files > 0
    assert len(result.ignorable_dirs) >= 2
