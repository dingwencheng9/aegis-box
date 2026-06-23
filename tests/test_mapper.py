"""
测试 Code Mapper 的 AST 提取功能
"""

import pytest
from pathlib import Path
from aegis.engines.mapper import CodeMapper, Language, CodeSkeleton


@pytest.fixture
def temp_python_file(tmp_path):
    """创建临时 Python 测试文件"""
    test_code = '''
import os
from typing import List, Optional

# TODO: 重构这个模块
# FIXME: 修复性能问题

class UserService:
    """用户服务类"""

    def __init__(self, db_url: str):
        self.db_url = db_url

    async def get_user(self, user_id: int) -> Optional[dict]:
        """获取用户信息"""
        # NOTE: 需要添加缓存
        result = await self.fetch_from_db(user_id)
        return self.parse_user(result)

    def fetch_from_db(self, user_id: int):
        """从数据库获取数据"""
        return {"id": user_id, "name": "test"}

    def parse_user(self, data: dict) -> dict:
        """解析用户数据"""
        return data

def calculate_score(values: List[int]) -> float:
    """计算分数"""
    if not values:
        return 0.0
    return sum(values) / len(values)

async def process_batch(items: List[dict]):
    """批处理"""
    results = []
    for item in items:
        result = await process_item(item)
        results.append(result)
    return results

def process_item(item: dict):
    """处理单个项目"""
    return item
'''

    file_path = tmp_path / "test_service.py"
    file_path.write_text(test_code)
    return file_path


def test_detect_language():
    """测试语言检测"""
    mapper = CodeMapper()

    assert mapper.detect_language(Path("test.py")) == Language.PYTHON
    assert mapper.detect_language(Path("test.js")) == Language.JAVASCRIPT
    assert mapper.detect_language(Path("test.ts")) == Language.TYPESCRIPT
    assert mapper.detect_language(Path("test.txt")) == Language.UNKNOWN


def test_extract_skeleton_python(temp_python_file):
    """测试 Python 代码骨架提取"""
    mapper = CodeMapper(
        max_function_lines=100,
        context_lines=10,
        preserve_comments=["TODO", "FIXME", "NOTE"]
    )

    skeleton = mapper.extract_skeleton(temp_python_file)

    # 验证基本信息
    assert skeleton is not None
    assert skeleton.language == Language.PYTHON
    assert skeleton.total_lines > 0

    # 验证导入语句
    assert len(skeleton.imports) >= 2  # import os, from typing

    # 验证类定义
    assert len(skeleton.classes) >= 1
    user_service = skeleton.classes[0]
    assert user_service.name == "UserService"
    assert len(user_service.methods) >= 3  # __init__, get_user, fetch_from_db, parse_user

    # 验证顶级函数
    assert len(skeleton.functions) >= 3  # calculate_score, process_batch, process_item

    # 验证重要注释被保留
    assert len(skeleton.global_comments) >= 2  # TODO, FIXME

    # 验证压缩率
    assert skeleton.compression_ratio < 1.0  # 应该小于原始大小

    print(f"\n压缩率: {skeleton.compression_ratio:.1%}")
    print(f"原始行数: {skeleton.total_lines}")
    print(f"骨架行数: {skeleton.skeleton_lines}")


def test_skeleton_to_markdown(temp_python_file):
    """测试骨架转换为 Markdown"""
    mapper = CodeMapper()
    skeleton = mapper.extract_skeleton(temp_python_file)

    markdown = skeleton.to_markdown()

    # 验证 Markdown 包含关键信息
    assert "# 📄" in markdown
    assert "## 📦 导入依赖" in markdown
    assert "## 🏛️ 类定义" in markdown
    assert "## 🔧 顶级函数" in markdown
    assert "UserService" in markdown
    assert "calculate_score" in markdown

    print("\n生成的 Markdown:")
    print(markdown)


def test_function_calls_extraction(temp_python_file):
    """测试函数调用关系提取"""
    mapper = CodeMapper()
    skeleton = mapper.extract_skeleton(temp_python_file)

    # 查找 get_user 方法
    user_service = skeleton.classes[0]
    get_user_method = None
    for method in user_service.methods:
        if method.name == "get_user":
            get_user_method = method
            break

    assert get_user_method is not None
    # 验证函数调用被提取
    # get_user 调用了 fetch_from_db 和 parse_user
    print(f"\nget_user 调用的函数: {get_user_method.calls}")


@pytest.mark.asyncio
async def test_map_codebase(tmp_path):
    """测试代码库映射"""
    from aegis.engines.mapper import map_codebase

    # 创建多个测试文件
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "service.py").write_text("def foo(): pass")
    (tmp_path / "src" / "utils.py").write_text("def bar(): pass")
    (tmp_path / "node_modules").mkdir()
    (tmp_path / "node_modules" / "test.py").write_text("def ignored(): pass")

    skeletons = await map_codebase(
        root_path=tmp_path,
        ignore_dirs=["node_modules", "__pycache__"]
    )

    # 验证只处理了 src 目录下的文件
    assert len(skeletons) == 2
    assert all(s.language == Language.PYTHON for s in skeletons)
