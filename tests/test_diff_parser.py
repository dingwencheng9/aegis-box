"""
测试 Diff Parser 的核心功能
"""

import pytest
from aegis.utils.diff_parser import (
    DiffParser,
    SearchReplaceBlock,
    PatchResult,
    MatchResult,
    PatchApplyError,
    parse_and_apply_patches,
)


# ==========================================
# Fixtures
# ==========================================
@pytest.fixture
def sample_source_code():
    """示例源代码"""
    return """def get_user(user_id):
    query = "SELECT * FROM users WHERE id = ?"
    result = db.execute(query, user_id)
    return result

def process_data(data):
    cleaned = clean(data)

    validated = validate(cleaned)

    return validated
"""


@pytest.fixture
def parser():
    """DiffParser 实例"""
    return DiffParser(similarity_threshold=0.85)


# ==========================================
# parse_llm_response 测试
# ==========================================
def test_parse_single_block(parser):
    """测试解析单个 SEARCH/REPLACE 块"""
    llm_output = """
<<<<<<< SEARCH
def old_function():
    pass
=======
def new_function():
    logger.info("updated")
>>>>>>> REPLACE
"""

    blocks = parser.parse_llm_response(llm_output)

    assert len(blocks) == 1
    assert blocks[0].search == "def old_function():\n    pass"
    assert blocks[0].replace == 'def new_function():\n    logger.info("updated")'


def test_parse_multiple_blocks(parser):
    """测试解析多个 SEARCH/REPLACE 块"""
    llm_output = """
Here's the fix:

<<<<<<< SEARCH
def func1():
    pass
=======
def func1():
    return 1
>>>>>>> REPLACE

And another change:

<<<<<<< SEARCH
def func2():
    pass
=======
def func2():
    return 2
>>>>>>> REPLACE
"""

    blocks = parser.parse_llm_response(llm_output)

    assert len(blocks) == 2
    assert "func1" in blocks[0].search
    assert "func2" in blocks[1].search


def test_parse_no_blocks(parser):
    """测试没有 SEARCH/REPLACE 块的情况"""
    llm_output = "Just some text without any blocks"

    blocks = parser.parse_llm_response(llm_output)

    assert len(blocks) == 0


# ==========================================
# Level 1: 精确匹配测试
# ==========================================
def test_exact_match(parser, sample_source_code):
    """测试精确匹配"""
    search_block = '''def get_user(user_id):
    query = "SELECT * FROM users WHERE id = ?"
    result = db.execute(query, user_id)
    return result'''

    result = parser.find_search_block(sample_source_code, search_block)

    assert result.found is True
    assert result.match_level == "exact"
    assert result.similarity == 1.0
    assert result.start_line == 0
    assert result.end_line == 4


# ==========================================
# Level 2: 空格忽略匹配测试
# ==========================================
def test_whitespace_insensitive_match(parser, sample_source_code):
    """测试忽略空格的匹配"""
    # 故意改变缩进
    search_block = '''def get_user(user_id):
  query = "SELECT * FROM users WHERE id = ?"
  result = db.execute(query, user_id)
  return result'''

    result = parser.find_search_block(sample_source_code, search_block)

    assert result.found is True
    assert result.match_level == "whitespace"
    assert result.similarity == 1.0


def test_whitespace_match_with_empty_lines(parser, sample_source_code):
    """测试忽略空行的匹配"""
    # LLM 省略了空行
    search_block = '''def process_data(data):
    cleaned = clean(data)
    validated = validate(cleaned)
    return validated'''

    result = parser.find_search_block(sample_source_code, search_block)

    assert result.found is True
    assert result.match_level == "whitespace"


# ==========================================
# Level 3: 模糊匹配测试
# ==========================================
def test_fuzzy_match_high_similarity(parser):
    """测试高相似度的模糊匹配"""
    source = """def calculate_total(items):
    total = 0
    for item in items:
        total += item.price
    return total"""

    # LLM 记错了一个变量名，但结构相似
    search_block = """def calculate_total(items):
    total = 0
    for item in items:
        total += item.cost
    return total"""

    result = parser.find_search_block(source, search_block)

    # 相似度应该 >= 85%
    assert result.found is True
    assert result.match_level == "fuzzy"
    assert result.similarity >= 0.85


def test_fuzzy_match_low_similarity(parser):
    """测试低相似度的模糊匹配（应该失败）"""
    source = """def func_a():
    return 1"""

    # 完全不同的代码
    search_block = """def func_b():
    return 2"""

    result = parser.find_search_block(source, search_block)

    assert result.found is False


# ==========================================
# normalize_code 测试
# ==========================================
def test_normalize_code(parser):
    """测试代码标准化和索引映射"""
    lines = [
        "def func():",
        "    pass",
        "",
        "    return None",
        ""
    ]

    normalized, index_map = parser._normalize_code(lines)

    assert normalized == ["def func():", "pass", "return None"]
    assert index_map == [0, 1, 3]  # 空行被跳过


def test_normalize_empty_code(parser):
    """测试空代码的标准化"""
    lines = ["", "", ""]

    normalized, index_map = parser._normalize_code(lines)

    assert normalized == []
    assert index_map == []


# ==========================================
# apply_patches 测试
# ==========================================
def test_apply_single_patch(parser):
    """测试应用单个补丁"""
    source = """def old_func():
    pass"""

    patch = SearchReplaceBlock(
        search="def old_func():\n    pass",
        replace="def new_func():\n    return 1",
        original_text="..."
    )

    result = parser.apply_patches(source, [patch])

    assert result.success is True
    assert result.applied_count == 1
    assert "def new_func():" in result.patched_code
    assert "def old_func():" not in result.patched_code


def test_apply_multiple_patches_reverse_order(parser):
    """测试多个补丁的倒序应用"""
    source = """line 1
line 2
line 3
line 4
line 5"""

    # 两个补丁：先匹配 line 2，再匹配 line 4
    patches = [
        SearchReplaceBlock(
            search="line 2",
            replace="LINE 2 UPDATED",
            original_text="..."
        ),
        SearchReplaceBlock(
            search="line 4",
            replace="LINE 4 UPDATED",
            original_text="..."
        )
    ]

    result = parser.apply_patches(source, patches)

    assert result.success is True
    assert result.applied_count == 2
    assert "LINE 2 UPDATED" in result.patched_code
    assert "LINE 4 UPDATED" in result.patched_code


def test_apply_patches_with_failure(parser):
    """测试部分补丁失败的情况"""
    source = """def func():
    pass"""

    patches = [
        SearchReplaceBlock(
            search="def func():\n    pass",
            replace="def func():\n    return 1",
            original_text="..."
        ),
        SearchReplaceBlock(
            search="def nonexistent():\n    pass",  # 不存在的代码
            replace="def new():\n    pass",
            original_text="..."
        )
    ]

    result = parser.apply_patches(source, patches)

    assert result.success is False
    assert result.applied_count == 1
    assert len(result.failed_blocks) == 1


def test_apply_empty_replace_block(parser):
    """测试空的 REPLACE 块（删除代码）"""
    source = """def func1():
    pass

def func2():
    pass"""

    patch = SearchReplaceBlock(
        search="def func1():\n    pass",
        replace="",  # 空的 REPLACE 块
        original_text="..."
    )

    result = parser.apply_patches(source, [patch])

    assert result.success is True
    assert "def func1():" not in result.patched_code
    assert "def func2():" in result.patched_code


# ==========================================
# 边界情况测试
# ==========================================
def test_empty_search_block(parser):
    """测试空的 SEARCH 块"""
    source = "some code"

    result = parser.find_search_block(source, "")

    assert result.found is False


def test_empty_source_code(parser):
    """测试空的源代码"""
    result = parser.find_search_block("", "search block")

    assert result.found is False


def test_search_longer_than_source(parser):
    """测试 SEARCH 块比源代码长"""
    source = "short"
    search_block = "this is a very long search block that is longer than the source"

    result = parser.find_search_block(source, search_block)

    assert result.found is False


# ==========================================
# parse_and_apply_patches 集成测试
# ==========================================
def test_parse_and_apply_patches_success():
    """测试完整的解析和应用流程（成功）"""
    source = """def old_function():
    pass"""

    llm_output = """
<<<<<<< SEARCH
def old_function():
    pass
=======
def new_function():
    return 1
>>>>>>> REPLACE
"""

    result = parse_and_apply_patches(source, llm_output)

    assert result.success is True
    assert result.applied_count == 1
    assert "def new_function():" in result.patched_code


def test_parse_and_apply_patches_no_blocks():
    """测试没有 SEARCH/REPLACE 块的情况"""
    source = "some code"
    llm_output = "Just some explanation without any blocks"

    result = parse_and_apply_patches(source, llm_output)

    assert result.success is False
    assert result.patched_code is None
    assert "未找到任何" in result.error_message


def test_compute_similarity(parser):
    """测试相似度计算"""
    seq1 = ["line1", "line2", "line3"]
    seq2 = ["line1", "line2", "line3"]

    similarity = parser._compute_similarity(seq1, seq2)
    assert similarity == 1.0

    seq3 = ["line1", "line2", "line4"]
    similarity = parser._compute_similarity(seq1, seq3)
    assert 0.6 < similarity < 0.9  # 部分相似
