"""
🛡️ Aegis - Smart Patcher（智能补丁引擎）
全自动代码修复引擎：大模型 + Diff Parser + Git Sandbox + AST Validator
"""

import ast
from pathlib import Path
from typing import List, Optional, Dict
from dataclasses import dataclass
from loguru import logger

from aegis.utils.diff_parser import parse_and_apply_patches, PatchApplyError
from aegis.utils.git_sandbox import create_sandbox
from aegis.core.llm import LLMClientFactory
from aegis.cli import AegisConfig


# ==========================================
# 数据模型
# ==========================================
@dataclass
class Vulnerability:
    """漏洞描述"""
    file_path: str
    description: str
    severity: str
    suggestion: str
    line_number: Optional[int] = None


@dataclass
class ArchitectureReport:
    """架构审计报告"""
    critical_vulnerabilities: List[Vulnerability]
    warnings: List[str] = None


@dataclass
class PatchResult:
    """补丁结果"""
    vulnerability: Vulnerability
    success: bool
    error_message: Optional[str] = None
    patched_code: Optional[str] = None


# ==========================================
# 智能补丁引擎
# ==========================================
class SmartPatcher:
    """
    智能补丁引擎

    职责：
    1. 遍历架构审计报告中的漏洞
    2. 为每个漏洞调用 Tier-3 大模型生成补丁
    3. 使用 Diff Parser 在内存中合并补丁
    4. 使用 AST Validator 验证语法
    5. 通过验证后，在 Git Sandbox 中安全写入
    6. 失败自动回滚，不影响其他修复

    Example:
        >>> patcher = SmartPatcher(repo_path=Path("/project"))
        >>> report = ArchitectureReport(critical_vulnerabilities=[...])
        >>> results = patcher.heal_vulnerabilities(report)
        >>> print(f"成功修复 {sum(r.success for r in results)} 个漏洞")
    """

    def __init__(
        self,
        config: AegisConfig,
        repo_path: Optional[Path] = None,
        auto_commit: bool = True
    ):
        """
        初始化智能补丁引擎

        Args:
            config: Aegis 全局配置
            repo_path: Git 仓库路径（默认当前目录）
            auto_commit: 是否自动提交成功的补丁
        """
        self.config = config
        self.repo_path = repo_path or Path.cwd()
        self.auto_commit = auto_commit

        # 初始化 LLM 客户端工厂
        self.llm_factory = LLMClientFactory(config)
        self._tier3_client = None  # 延迟初始化

    @property
    def tier3_client(self):
        """延迟初始化 Tier-3 客户端"""
        if self._tier3_client is None:
            self._tier3_client = self.llm_factory.create_tier3_client()
        return self._tier3_client

    async def heal_vulnerabilities(
        self,
        report: ArchitectureReport
    ) -> List[PatchResult]:
        """
        修复架构报告中的所有关键漏洞

        核心策略：
        - 每个漏洞单独开启一个 Git Sandbox
        - 失败回滚，不影响其他修复
        - 内存级合并 + AST 验证

        Args:
            report: 架构审计报告

        Returns:
            修复结果列表
        """
        logger.info(
            f"🚀 开始修复 {len(report.critical_vulnerabilities)} 个关键漏洞..."
        )

        results = []

        for idx, vuln in enumerate(report.critical_vulnerabilities, 1):
            logger.info(
                f"\n{'='*80}\n"
                f"[{idx}/{len(report.critical_vulnerabilities)}] "
                f"修复漏洞: {vuln.description}\n"
                f"{'='*80}"
            )

            result = await self._fix_single_vulnerability(vuln)
            results.append(result)

            if result.success:
                logger.success(f"✅ 漏洞已修复: {vuln.file_path}")
            else:
                logger.error(f"❌ 漏洞修复失败: {result.error_message}")

        # 统计结果
        success_count = sum(r.success for r in results)
        failure_count = len(results) - success_count

        logger.info(
            f"\n{'='*80}\n"
            f"🎯 修复完成！\n"
            f"  成功: {success_count} 个\n"
            f"  失败: {failure_count} 个\n"
            f"{'='*80}"
        )

        return results

    async def _fix_single_vulnerability(
        self,
        vuln: Vulnerability
    ) -> PatchResult:
        """
        修复单个漏洞（细粒度沙盒包裹）

        步骤：
        1. 检查文件是否存在
        2. 读取文件内容
        3. 调用 Tier-3 模型生成补丁
        4. 在内存中合并补丁
        5. AST 语法验证
        6. 在 Git Sandbox 中安全写入

        Args:
            vuln: 漏洞描述

        Returns:
            PatchResult: 修复结果
        """
        # Security: 验证路径不越界
        try:
            file_path = (self.repo_path / vuln.file_path).resolve()
            if not file_path.is_relative_to(self.repo_path.resolve()):
                logger.error(f"🚨 路径遍历检测: {vuln.file_path}")
                return PatchResult(
                    vulnerability=vuln,
                    success=False,
                    error_message=f"Security: Path traversal detected"
                )
        except (ValueError, OSError) as e:
            logger.error(f"🚨 路径解析失败: {e}")
            return PatchResult(
                vulnerability=vuln,
                success=False,
                error_message=f"Invalid path: {e}"
            )

        # Step 1: 检查文件是否存在
        if not file_path.exists():
            logger.warning(f"⚠️  文件不存在，跳过: {vuln.file_path}")
            return PatchResult(
                vulnerability=vuln,
                success=False,
                error_message=f"文件不存在: {vuln.file_path}"
            )

        # Step 2: 读取文件内容
        try:
            source_code = file_path.read_text(encoding="utf-8")
        except Exception as e:
            logger.error(f"❌ 读取文件失败: {e}")
            return PatchResult(
                vulnerability=vuln,
                success=False,
                error_message=f"读取文件失败: {e}"
            )

        # Step 3: 细粒度沙盒包裹（One Sandbox Per Fix）
        try:
            with create_sandbox(
                repo_path=self.repo_path,
                auto_commit=self.auto_commit,
                commit_message=f"fix: {vuln.description}"
            ):
                # Step 4: 调用 Tier-3 模型生成补丁
                logger.info("🤖 调用 Tier-3 模型生成补丁...")
                llm_output = await self._generate_patch(vuln, source_code)

                # Step 5: 在内存中合并补丁
                logger.info("🔧 在内存中合并补丁...")
                patch_result = parse_and_apply_patches(
                    source_code,
                    llm_output,
                    similarity_threshold=0.85
                )

                if not patch_result.success:
                    raise PatchApplyError(
                        f"补丁合并失败: {patch_result.error_message}"
                    )

                patched_code = patch_result.patched_code

                # Step 6: AST 语法验证
                logger.info("✅ 执行 AST 语法验证...")
                self._validate_syntax(patched_code, vuln.file_path)

                # Step 7: 通过验证，安全写入文件
                logger.info("💾 写入文件...")
                file_path.write_text(patched_code, encoding="utf-8")

                logger.success("🎉 补丁已成功应用并通过语法验证")

                return PatchResult(
                    vulnerability=vuln,
                    success=True,
                    patched_code=patched_code
                )

        except PatchApplyError as e:
            logger.error(f"❌ 补丁应用失败: {e}")
            return PatchResult(
                vulnerability=vuln,
                success=False,
                error_message=f"补丁应用失败: {e}"
            )
        except SyntaxError as e:
            logger.error(f"❌ 语法验证失败: {e}")
            return PatchResult(
                vulnerability=vuln,
                success=False,
                error_message=f"语法验证失败: {e}"
            )
        except Exception as e:
            logger.error(f"❌ 未知错误: {e}")
            return PatchResult(
                vulnerability=vuln,
                success=False,
                error_message=f"未知错误: {e}"
            )

    async def _generate_patch(
        self,
        vuln: Vulnerability,
        file_content: str
    ) -> str:
        """
        调用 Tier-3 大模型生成补丁

        Args:
            vuln: 漏洞描述
            file_content: 原文件内容

        Returns:
            LLM 输出（包含 SEARCH/REPLACE 块）
        """
        # 构建 Prompt
        prompt = self._build_patch_prompt(vuln, file_content)

        # 🔥 调用 Tier-3 LLM（异步 + 结构化输出）
        try:
            response = await self.tier3_client.chat(
                prompt=prompt,
                system_prompt=(
                    "你是一个资深的底层安全修补专家。\n"
                    "你的任务是生成精确的代码补丁。\n\n"
                    "输出格式要求（极其严格）：\n"
                    "1. 只能输出 SEARCH/REPLACE 块格式\n"
                    "2. 格式如下：\n"
                    "<<<<<<< SEARCH\n"
                    "(old code)\n"
                    "=======\n"
                    "(new code)\n"
                    ">>>>>>> REPLACE\n\n"
                    "3. 绝对不允许输出任何解释、寒暄或 Markdown 标记\n"
                    "4. 不要添加任何额外的文字说明\n"
                    "5. 确保生成的代码语法正确\n"
                    "6. 保持原代码的缩进风格\n"
                    "7. 如果需要多个修改，输出多个 SEARCH/REPLACE 块"
                ),
                max_tokens=4000,
                temperature=0.2  # 低温度，减少幻觉
            )

            logger.success("✅ Tier-3 模型已返回补丁")
            return response

        except Exception as e:
            logger.error(f"❌ 调用 Tier-3 模型失败: {e}")
            raise PatchApplyError(f"调用 Tier-3 模型失败: {e}") from e

    def _build_patch_prompt(
        self,
        vuln: Vulnerability,
        file_content: str
    ) -> str:
        """
        构建补丁生成 Prompt

        Args:
            vuln: 漏洞描述
            file_content: 原文件内容

        Returns:
            完整的 Prompt
        """
        # 防御性工程：长字符串折行
        prompt = (
            f"文件路径: {vuln.file_path}\n\n"
            f"漏洞描述:\n{vuln.description}\n\n"
            f"严重程度: {vuln.severity}\n\n"
            f"修复建议:\n{vuln.suggestion}\n\n"
            f"原文件内容:\n"
            f"```\n{file_content}\n```\n\n"
            f"请生成修复此漏洞的 SEARCH/REPLACE 块。\n"
            f"要求：\n"
            f"1. 只输出 SEARCH/REPLACE 块，不要有任何解释\n"
            f"2. SEARCH 块必须精确匹配原文件中的代码\n"
            f"3. REPLACE 块包含修复后的代码\n"
            f"4. 确保修复后的代码语法正确\n"
            f"5. 保持原代码的缩进和格式"
        )

        return prompt

    def _validate_syntax(
        self,
        code: str,
        file_path: str
    ):
        """
        AST 语法验证（内存级安检门）

        对 Python 文件执行 ast.parse() 验证语法

        Args:
            code: 代码内容
            file_path: 文件路径

        Raises:
            SyntaxError: 语法错误（触发沙盒回滚）
        """
        # 只验证 Python 文件
        if not file_path.endswith(".py"):
            logger.debug(f"跳过非 Python 文件的语法验证: {file_path}")
            return

        try:
            # AST 解析
            ast.parse(code)
            logger.success("✅ AST 语法验证通过")

        except SyntaxError as e:
            logger.error(
                f"❌ AST 语法验证失败:\n"
                f"  文件: {file_path}\n"
                f"  行号: {e.lineno}\n"
                f"  错误: {e.msg}"
            )
            raise SyntaxError(
                f"大模型生成的代码存在语法错误 (行 {e.lineno}): {e.msg}"
            ) from e


# ==========================================
# 外部调用入口
# ==========================================
def heal_project_vulnerabilities(
    report: ArchitectureReport,
    repo_path: Optional[Path] = None,
    auto_commit: bool = True
) -> List[PatchResult]:
    """
    修复项目中的所有漏洞（一站式入口）

    Args:
        report: 架构审计报告
        repo_path: Git 仓库路径（默认当前目录）
        auto_commit: 是否自动提交成功的补丁

    Returns:
        修复结果列表

    Example:
        >>> from aegis.engines.reducer import ArchitectureReducer
        >>> from aegis.engines.patcher import heal_project_vulnerabilities
        >>>
        >>> # Step 1: 生成架构报告
        >>> reducer = ArchitectureReducer()
        >>> report = reducer.reduce("/path/to/project")
        >>>
        >>> # Step 2: 自动修复漏洞
        >>> results = heal_project_vulnerabilities(report)
        >>>
        >>> # Step 3: 查看结果
        >>> for result in results:
        ...     print(f"{result.vulnerability.description}: {result.success}")
    """
    patcher = SmartPatcher(repo_path=repo_path, auto_commit=auto_commit)
    return patcher.heal_vulnerabilities(report)
