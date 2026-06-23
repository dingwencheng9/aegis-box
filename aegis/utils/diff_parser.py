"""
🛡️ Aegis - Diff Parser（差异解析器）
解析 LLM 输出的 SEARCH/REPLACE 块并安全地应用到源代码
"""

import re
from typing import List, Tuple, Optional
from dataclasses import dataclass
from difflib import SequenceMatcher
from loguru import logger


# ==========================================
# 异常定义
# ==========================================
class PatchApplyError(Exception):
    """补丁应用失败异常"""
    pass


# ==========================================
# 数据模型
# ==========================================
@dataclass
class SearchReplaceBlock:
    """SEARCH/REPLACE 块"""
    search: str
    replace: str
    original_text: str  # 原始文本（用于调试）


@dataclass
class PatchResult:
    """补丁应用结果"""
    success: bool
    patched_code: Optional[str]
    applied_count: int
    failed_blocks: List[SearchReplaceBlock]
    error_message: Optional[str] = None


@dataclass
class MatchResult:
    """匹配结果"""
    found: bool
    start_line: int
    end_line: int
    similarity: float
    match_level: str  # "exact" | "whitespace" | "fuzzy"


# ==========================================
# 核心类：差异解析器
# ==========================================
class DiffParser:
    """
    差异解析器

    职责：
    1. 解析 LLM 输出的 SEARCH/REPLACE 块
    2. 三级匹配策略（精确 -> 空格忽略 -> 模糊）
    3. 安全地应用补丁到源代码
    """

    def __init__(
        self,
        similarity_threshold: float = 0.85,
        window_size_tolerance: float = 0.2,
    ):
        """
        初始化差异解析器

        Args:
            similarity_threshold: 模糊匹配的相似度阈值（默认 85%）
            window_size_tolerance: 窗口大小容忍度（默认 ±20%）
        """
        self.similarity_threshold = similarity_threshold
        self.window_size_tolerance = window_size_tolerance

    def parse_llm_response(self, text: str) -> List[SearchReplaceBlock]:
        """
        从 LLM 响应中提取所有 SEARCH/REPLACE 块

        格式：
        <<<<<<< SEARCH
        (old code)
        =======
        (new code)
        >>>>>>> REPLACE

        Args:
            text: LLM 的完整响应文本

        Returns:
            SearchReplaceBlock 列表
        """
        # 正则表达式：提取所有 SEARCH/REPLACE 块（允许空块）
        pattern = r'<<<<<<< SEARCH\s*\n(.*?)\n=======\s*\n(.*?)\n>>>>>>> REPLACE'
        matches = re.findall(pattern, text, re.DOTALL)

        blocks = []
        for search_content, replace_content in matches:
            original = f"<<<<<<< SEARCH\n{search_content}\n=======\n{replace_content}\n>>>>>>> REPLACE"
            blocks.append(
                SearchReplaceBlock(
                    search=search_content,
                    replace=replace_content,
                    original_text=original
                )
            )

        logger.info(f"从 LLM 响应中提取到 {len(blocks)} 个 SEARCH/REPLACE 块")
        return blocks

    def apply_patches(
        self,
        source_code: str,
        patches: List[SearchReplaceBlock]
    ) -> PatchResult:
        """
        应用多个补丁到源代码（从下往上替换）

        Args:
            source_code: 原始源代码
            patches: SEARCH/REPLACE 块列表

        Returns:
            PatchResult: 补丁应用结果
        """
        if not patches:
            return PatchResult(
                success=True,
                patched_code=source_code,
                applied_count=0,
                failed_blocks=[]
            )

        # Step 1: 计算每个补丁的匹配位置
        patch_positions = []
        failed_blocks = []

        for idx, patch in enumerate(patches):
            try:
                match_result = self.find_search_block(source_code, patch.search)

                if match_result.found:
                    patch_positions.append((patch, match_result))
                    logger.success(
                        f"✅ 补丁 #{idx+1} 找到匹配 (L{match_result.start_line}-L{match_result.end_line}, "
                        f"{match_result.match_level}, {match_result.similarity:.2%})"
                    )
                else:
                    failed_blocks.append(patch)
                    logger.error(f"❌ 补丁 #{idx+1} 未找到匹配的 SEARCH 块")
            except Exception as e:
                failed_blocks.append(patch)
                logger.error(f"❌ 补丁 #{idx+1} 处理失败: {e}")

        # Step 2: 按照 start_line 降序排序（从下往上替换，避免行号错位）
        patch_positions.sort(key=lambda x: x[1].start_line, reverse=True)

        # Step 3: 逐个应用补丁（从下往上）
        source_lines = source_code.split('\n')

        for patch, match_result in patch_positions:
            # 处理空的 REPLACE 块（删除代码）
            if not patch.replace.strip():
                replacement = []
            else:
                replacement = patch.replace.split('\n')

            # 替换代码块
            before = source_lines[:match_result.start_line]
            after = source_lines[match_result.end_line:]

            source_lines = before + replacement + after

            logger.info(
                f"🔧 已应用补丁: L{match_result.start_line}-L{match_result.end_line} "
                f"({len(replacement)} 行替换)"
            )

        # Step 4: 返回结果
        patched_code = '\n'.join(source_lines)

        return PatchResult(
            success=len(failed_blocks) == 0,
            patched_code=patched_code,
            applied_count=len(patch_positions),
            failed_blocks=failed_blocks
        )

    def find_search_block(
        self,
        source_code: str,
        search_block: str
    ) -> MatchResult:
        """
        三级匹配策略：精确 -> 空格忽略 -> 模糊

        Args:
            source_code: 源代码
            search_block: SEARCH 块内容

        Returns:
            MatchResult: 匹配结果
        """
        # 边界检查：空的 SEARCH 块（添加新代码的场景）
        if not search_block.strip():
            logger.warning("⚠️  SEARCH 块为空，跳过匹配（可能是添加新代码的场景）")
            return MatchResult(
                found=False,
                start_line=-1,
                end_line=-1,
                similarity=0.0,
                match_level="none"
            )

        source_lines = source_code.split('\n')

        # Level 1: 精确匹配
        result = self._exact_match(source_lines, search_block)
        if result.found:
            return result

        # Level 2: 忽略空格匹配
        result = self._whitespace_insensitive_match(source_lines, search_block)
        if result.found:
            return result

        # Level 3: 模糊匹配（滑动窗口）
        result = self._fuzzy_match(source_lines, search_block)
        if result.found:
            return result

        # 所有匹配都失败
        return MatchResult(
            found=False,
            start_line=-1,
            end_line=-1,
            similarity=0.0,
            match_level="none"
        )

    def _exact_match(
        self,
        source_lines: List[str],
        search_block: str
    ) -> MatchResult:
        """
        Level 1: 精确匹配

        Args:
            source_lines: 源文件行列表
            search_block: SEARCH 块内容

        Returns:
            MatchResult: 匹配结果
        """
        source_code = '\n'.join(source_lines)
        start_idx = source_code.find(search_block)

        if start_idx != -1:
            # 计算行号
            before_match = source_code[:start_idx]
            start_line = before_match.count('\n')
            end_line = start_line + search_block.count('\n') + 1

            logger.debug(f"Level 1 精确匹配成功: L{start_line}-L{end_line}")

            return MatchResult(
                found=True,
                start_line=start_line,
                end_line=end_line,
                similarity=1.0,
                match_level="exact"
            )

        return MatchResult(
            found=False,
            start_line=-1,
            end_line=-1,
            similarity=0.0,
            match_level="exact"
        )

    def _whitespace_insensitive_match(
        self,
        source_lines: List[str],
        search_block: str
    ) -> MatchResult:
        """
        Level 2: 忽略空格和缩进的匹配

        Args:
            source_lines: 源文件行列表
            search_block: SEARCH 块内容

        Returns:
            MatchResult: 匹配结果
        """
        # 标准化 SEARCH 块
        search_lines = search_block.split('\n')
        norm_search, _ = self._normalize_code(search_lines)

        # 标准化源文件（带索引映射）
        norm_source, index_map = self._normalize_code(source_lines)

        # 边界检查
        search_len = len(norm_search)
        if search_len == 0 or len(norm_source) == 0:
            return MatchResult(
                found=False,
                start_line=-1,
                end_line=-1,
                similarity=0.0,
                match_level="whitespace"
            )

        # 查找连续匹配
        for i in range(len(norm_source) - search_len + 1):
            window = norm_source[i:i + search_len]

            if window == norm_search:
                # 找到匹配，O(1) 反向映射到原始行号
                start_line = index_map[i]
                end_line = index_map[i + search_len - 1] + 1

                logger.debug(f"Level 2 空格忽略匹配成功: L{start_line}-L{end_line}")

                return MatchResult(
                    found=True,
                    start_line=start_line,
                    end_line=end_line,
                    similarity=1.0,
                    match_level="whitespace"
                )

        return MatchResult(
            found=False,
            start_line=-1,
            end_line=-1,
            similarity=0.0,
            match_level="whitespace"
        )

    def _fuzzy_match(
        self,
        source_lines: List[str],
        search_block: str
    ) -> MatchResult:
        """
        Level 3: 模糊匹配（滑动窗口 + 相似度）

        Args:
            source_lines: 源文件行列表
            search_block: SEARCH 块内容

        Returns:
            MatchResult: 匹配结果
        """
        # 标准化
        search_lines = search_block.split('\n')
        norm_search, _ = self._normalize_code(search_lines)
        norm_source, index_map = self._normalize_code(source_lines)

        # 边界检查
        if not norm_search or not norm_source:
            return MatchResult(
                found=False,
                start_line=-1,
                end_line=-1,
                similarity=0.0,
                match_level="fuzzy"
            )

        # 窗口大小范围：SEARCH 行数 ± tolerance
        search_len = len(norm_search)
        min_window = max(1, int(search_len * (1 - self.window_size_tolerance)))
        max_window = min(
            int(search_len * (1 + self.window_size_tolerance)),
            len(norm_source)  # 不超过源文件长度
        )

        best_match = None
        best_similarity = 0.0

        # 滑动窗口扫描
        for window_size in range(min_window, max_window + 1):
            # 边界检查：确保窗口不超出范围
            if window_size > len(norm_source):
                continue

            for start_idx in range(len(norm_source) - window_size + 1):
                end_idx = start_idx + window_size
                window = norm_source[start_idx:end_idx]

                # 计算相似度
                similarity = self._compute_similarity(norm_search, window)

                if similarity > best_similarity:
                    best_similarity = similarity
                    best_match = (start_idx, end_idx)

        # 检查阈值
        if best_match and best_similarity >= self.similarity_threshold:
            start_idx, end_idx = best_match

            # O(1) 反向映射（边界检查）
            if start_idx >= len(index_map) or end_idx - 1 >= len(index_map):
                logger.error("❌ 索引映射越界，回退到失败状态")
                return MatchResult(
                    found=False,
                    start_line=-1,
                    end_line=-1,
                    similarity=best_similarity,
                    match_level="fuzzy"
                )

            start_line = index_map[start_idx]
            end_line = index_map[end_idx - 1] + 1

            logger.debug(
                f"Level 3 模糊匹配成功: L{start_line}-L{end_line} "
                f"(相似度 {best_similarity:.2%})"
            )

            return MatchResult(
                found=True,
                start_line=start_line,
                end_line=end_line,
                similarity=best_similarity,
                match_level="fuzzy"
            )

        logger.debug(f"Level 3 模糊匹配失败 (最佳相似度 {best_similarity:.2%})")

        return MatchResult(
            found=False,
            start_line=-1,
            end_line=-1,
            similarity=best_similarity,
            match_level="fuzzy"
        )

    def _normalize_code(
        self,
        lines: List[str]
    ) -> Tuple[List[str], List[int]]:
        """
        标准化代码（移除空行和首尾空格）+ O(1) 索引映射

        Args:
            lines: 原始代码行列表

        Returns:
            (normalized_lines, index_map)
            - normalized_lines: 标准化后的代码行
            - index_map: normalized_lines[i] 对应的原始行号
        """
        normalized = []
        index_map = []

        for i, line in enumerate(lines):
            stripped = line.strip()

            # 跳过空行
            if not stripped:
                continue

            normalized.append(stripped)
            index_map.append(i)  # O(1) 记录原始行号

        return normalized, index_map

    def _compute_similarity(
        self,
        seq1: List[str],
        seq2: List[str]
    ) -> float:
        """
        计算两个代码序列的相似度

        Args:
            seq1: 第一个代码行列表
            seq2: 第二个代码行列表

        Returns:
            相似度 (0.0 - 1.0)
        """
        matcher = SequenceMatcher(None, seq1, seq2)
        return matcher.ratio()


# ==========================================
# 外部调用入口
# ==========================================
def parse_and_apply_patches(
    source_code: str,
    llm_response: str,
    similarity_threshold: float = 0.85
) -> PatchResult:
    """
    解析 LLM 响应并应用补丁的一站式入口

    Args:
        source_code: 原始源代码
        llm_response: LLM 的完整响应文本
        similarity_threshold: 模糊匹配阈值（默认 85%）

    Returns:
        PatchResult: 补丁应用结果

    Example:
        >>> source = open("user.py").read()
        >>> llm_output = '''
        ... <<<<<<< SEARCH
        ... def old_function():
        ...     pass
        ... =======
        ... def new_function():
        ...     logger.info("updated")
        ... >>>>>>> REPLACE
        ... '''
        >>> result = parse_and_apply_patches(source, llm_output)
        >>> if result.success:
        ...     open("user.py", "w").write(result.patched_code)
    """
    parser = DiffParser(similarity_threshold=similarity_threshold)

    # Step 1: 提取 SEARCH/REPLACE 块
    patches = parser.parse_llm_response(llm_response)

    if not patches:
        logger.warning("⚠️  未找到任何 SEARCH/REPLACE 块")
        return PatchResult(
            success=False,
            patched_code=None,
            applied_count=0,
            failed_blocks=[],
            error_message="未找到任何 SEARCH/REPLACE 块"
        )

    # Step 2: 应用补丁
    result = parser.apply_patches(source_code, patches)

    # Step 3: 日志输出
    if result.success:
        logger.success(f"🎉 补丁应用成功！共应用 {result.applied_count} 个块")
    else:
        logger.error(
            f"❌ 补丁应用部分失败！成功 {result.applied_count} 个，"
            f"失败 {len(result.failed_blocks)} 个"
        )

    return result
