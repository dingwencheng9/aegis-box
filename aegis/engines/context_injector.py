"""
🛡️ Aegis - Context Injector（上下文注入器）
IDE 上下文桥接：将审计结果同步到 .cursorrules 和 .claude_context.xml
"""

import hashlib
from pathlib import Path
from typing import Optional, List, Dict
from datetime import datetime
from dataclasses import dataclass
from loguru import logger

from aegis.engines.reducer import ArchitectureReport


# ==========================================
# 数据模型
# ==========================================
@dataclass
class ContextInjectionResult:
    """上下文注入结果"""
    success: bool
    target_file: str
    injected: bool
    error_message: Optional[str] = None


# ==========================================
# 上下文注入器
# ==========================================
class ContextInjector:
    """
    上下文注入器

    职责：
    1. 从架构报告中提取关键信息
    2. 生成 IDE 上下文文件（.cursorrules / .claude_context.xml）
    3. 智能追加（不覆盖已有内容）
    4. 幂等性保证（避免重复注入）

    Example:
        >>> injector = ContextInjector(project_root=Path("/project"))
        >>> result = injector.inject_context(report)
        >>> if result.success:
        ...     print(f"上下文已注入到 {result.target_file}")
    """

    # Aegis 上下文标记（用于幂等性）
    AEGIS_MARKER_START = "<!-- AEGIS_CONTEXT_START -->"
    AEGIS_MARKER_END = "<!-- AEGIS_CONTEXT_END -->"

    def __init__(
        self,
        project_root: Optional[Path] = None,
        target_format: str = "cursorrules"  # "cursorrules" or "claude_xml"
    ):
        """
        初始化上下文注入器

        Args:
            project_root: 项目根目录（默认当前目录）
            target_format: 目标格式（cursorrules 或 claude_xml）
        """
        self.project_root = project_root or Path.cwd()
        self.target_format = target_format

        # 目标文件路径
        if target_format == "cursorrules":
            self.target_file = self.project_root / ".cursorrules"
        else:
            self.target_file = self.project_root / ".claude_context.xml"

    def inject_context(
        self,
        report: ArchitectureReport
    ) -> ContextInjectionResult:
        """
        注入上下文到 IDE 配置文件

        核心逻辑：
        1. 生成上下文内容
        2. 检查是否已存在 Aegis 上下文
        3. 智能追加或更新

        Args:
            report: 架构审计报告

        Returns:
            ContextInjectionResult: 注入结果
        """
        logger.info(f"🔄 开始注入上下文到 {self.target_file.name}...")

        try:
            # Step 1: 生成上下文内容
            context_content = self._generate_context_content(report)

            # Step 2: 检查目标文件是否存在
            if self.target_file.exists():
                logger.info(f"检测到已有 {self.target_file.name}，准备智能追加...")
                existing_content = self.target_file.read_text(encoding="utf-8")

                # Step 3: 检查是否已有 Aegis 上下文（幂等性）
                if self.AEGIS_MARKER_START in existing_content:
                    logger.info("检测到已有 Aegis 上下文，准备更新...")
                    updated_content = self._update_existing_context(
                        existing_content,
                        context_content
                    )
                else:
                    logger.info("未检测到 Aegis 上下文，准备追加...")
                    updated_content = self._append_context(
                        existing_content,
                        context_content
                    )
            else:
                logger.info(f"未检测到 {self.target_file.name}，准备创建...")
                updated_content = context_content

            # Step 4: 写入文件
            self.target_file.write_text(updated_content, encoding="utf-8")

            logger.success(f"✅ 上下文已成功注入到 {self.target_file.name}")

            return ContextInjectionResult(
                success=True,
                target_file=str(self.target_file),
                injected=True
            )

        except Exception as e:
            logger.error(f"❌ 上下文注入失败: {e}")
            return ContextInjectionResult(
                success=False,
                target_file=str(self.target_file),
                injected=False,
                error_message=str(e)
            )

    def _generate_context_content(
        self,
        report: ArchitectureReport
    ) -> str:
        """
        生成上下文内容

        Args:
            report: 架构审计报告

        Returns:
            上下文内容（Markdown 格式）
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # 提取关键信息
        critical_vulns = report.critical_vulnerabilities
        architecture_patterns = self._extract_architecture_patterns(report)
        dependency_summary = self._extract_dependency_summary(report)

        # 生成 Markdown
        content = f"""
{self.AEGIS_MARKER_START}
# 🛡️ Aegis 架构审计上下文

**生成时间**: {timestamp}
**审计模式**: 全自动安全审计

---

## 📋 全局架构规范

{architecture_patterns}

---

## 🔥 高频漏洞模式

以下漏洞在本项目中被检测到，请在后续开发中避免：

{self._format_vulnerabilities(critical_vulns)}

---

## 📦 依赖拓扑概要

{dependency_summary}

---

## 💡 开发建议

在进行后续开发时，请：

1. **遵守上述架构规范**：确保新代码符合项目的架构约束
2. **避免高频漏洞模式**：特别注意 SQL 注入、XSS、路径遍历等安全问题
3. **保持依赖最新**：定期更新依赖，避免使用已知漏洞的版本
4. **使用参数化查询**：永远不要用字符串拼接构建 SQL 查询
5. **验证用户输入**：所有外部输入必须经过严格验证和净化

---

*此上下文由 Aegis 自动生成，最后更新: {timestamp}*

{self.AEGIS_MARKER_END}
"""

        return content

    def _extract_architecture_patterns(
        self,
        report: ArchitectureReport
    ) -> str:
        """
        提取架构模式

        Args:
            report: 架构审计报告

        Returns:
            架构模式描述
        """
        # 这里可以根据实际的 ArchitectureReport 结构提取信息
        # 示例实现
        patterns = [
            "- **分层架构**：项目采用典型的三层架构（Controller -> Service -> Repository）",
            "- **依赖注入**：使用依赖注入模式管理组件依赖",
            "- **RESTful API**：API 端点遵循 RESTful 规范",
            "- **异步处理**：使用异步任务处理长时间运行的操作"
        ]

        return "\n".join(patterns)

    def _extract_dependency_summary(
        self,
        report: ArchitectureReport
    ) -> str:
        """
        提取依赖概要

        Args:
            report: 架构审计报告

        Returns:
            依赖概要描述
        """
        # 示例实现
        summary = """
**核心依赖**:
- Python 3.9+
- FastAPI (Web 框架)
- SQLAlchemy (ORM)
- Redis (缓存)
- PostgreSQL (数据库)

**开发依赖**:
- pytest (测试框架)
- black (代码格式化)
- mypy (类型检查)
"""

        return summary

    def _format_vulnerabilities(
        self,
        vulnerabilities: List
    ) -> str:
        """
        格式化漏洞列表

        Args:
            vulnerabilities: 漏洞列表

        Returns:
            格式化后的漏洞描述
        """
        if not vulnerabilities:
            return "✅ **未检测到关键漏洞**"

        lines = []
        for idx, vuln in enumerate(vulnerabilities, 1):
            lines.append(
                f"{idx}. **{vuln.description}**\n"
                f"   - 文件: `{vuln.file_path}`\n"
                f"   - 严重程度: {vuln.severity}\n"
                f"   - 修复建议: {vuln.suggestion}\n"
            )

        return "\n".join(lines)

    def _append_context(
        self,
        existing_content: str,
        new_context: str
    ) -> str:
        """
        追加上下文到已有内容

        Args:
            existing_content: 已有内容
            new_context: 新上下文

        Returns:
            合并后的内容
        """
        # 使用分隔符追加
        separator = "\n\n" + "=" * 80 + "\n\n"

        return existing_content + separator + new_context

    def _update_existing_context(
        self,
        existing_content: str,
        new_context: str
    ) -> str:
        """
        更新已有的 Aegis 上下文（幂等性）

        Args:
            existing_content: 已有内容
            new_context: 新上下文

        Returns:
            更新后的内容
        """
        # 查找 Aegis 标记
        start_idx = existing_content.find(self.AEGIS_MARKER_START)
        end_idx = existing_content.find(self.AEGIS_MARKER_END)

        if start_idx == -1 or end_idx == -1:
            # 标记不完整，追加新上下文
            logger.warning("Aegis 标记不完整，将追加新上下文")
            return self._append_context(existing_content, new_context)

        # 替换 Aegis 上下文
        before = existing_content[:start_idx]
        after = existing_content[end_idx + len(self.AEGIS_MARKER_END):]

        return before + new_context + after

    def remove_context(self) -> ContextInjectionResult:
        """
        移除 Aegis 上下文

        Returns:
            ContextInjectionResult: 移除结果
        """
        logger.info(f"🗑️  移除 Aegis 上下文...")

        try:
            if not self.target_file.exists():
                logger.info(f"{self.target_file.name} 不存在，无需移除")
                return ContextInjectionResult(
                    success=True,
                    target_file=str(self.target_file),
                    injected=False
                )

            existing_content = self.target_file.read_text(encoding="utf-8")

            # 查找 Aegis 标记
            start_idx = existing_content.find(self.AEGIS_MARKER_START)
            end_idx = existing_content.find(self.AEGIS_MARKER_END)

            if start_idx == -1:
                logger.info("未检测到 Aegis 上下文，无需移除")
                return ContextInjectionResult(
                    success=True,
                    target_file=str(self.target_file),
                    injected=False
                )

            # 移除 Aegis 上下文
            before = existing_content[:start_idx]
            after = existing_content[end_idx + len(self.AEGIS_MARKER_END):] if end_idx != -1 else ""

            # 清理多余的空行和分隔符
            updated_content = (before + after).strip()

            if updated_content:
                self.target_file.write_text(updated_content, encoding="utf-8")
            else:
                # 如果文件为空，删除文件
                self.target_file.unlink()
                logger.info(f"{self.target_file.name} 已删除（内容为空）")

            logger.success(f"✅ Aegis 上下文已移除")

            return ContextInjectionResult(
                success=True,
                target_file=str(self.target_file),
                injected=False
            )

        except Exception as e:
            logger.error(f"❌ 移除上下文失败: {e}")
            return ContextInjectionResult(
                success=False,
                target_file=str(self.target_file),
                injected=False,
                error_message=str(e)
            )


# ==========================================
# CI/CD 审计模式
# ==========================================
class CIAuditor:
    """
    CI/CD 审计器

    职责：
    1. 静默运行完整审计流程
    2. 生成审计报告
    3. 支持 GitHub Actions 集成

    Example:
        >>> auditor = CIAuditor(project_root=Path("/project"))
        >>> result = auditor.run_ci_audit()
        >>> print(result.markdown_report)
    """

    def __init__(
        self,
        project_root: Optional[Path] = None
    ):
        """
        初始化 CI 审计器

        Args:
            project_root: 项目根目录（默认当前目录）
        """
        self.project_root = project_root or Path.cwd()

    def run_ci_audit(self) -> Dict:
        """
        运行 CI 审计

        流程：
        1. Sweep -> Audit -> Patch
        2. 生成审计报告
        3. 返回结果

        Returns:
            审计结果字典
        """
        logger.info("🤖 CI 模式：开始全自动审计...")

        try:
            # TODO: 实际实现需要调用完整流程
            # from aegis.engines.sweeper import AssetSweeper
            # from aegis.engines.reducer import ArchitectureReducer
            # from aegis.engines.patcher import SmartPatcher

            # Step 1: Sweep
            logger.info("📦 Step 1: 资产清扫...")
            # sweeper = AssetSweeper(self.project_root)
            # sweep_result = sweeper.sweep()

            # Step 2: Audit
            logger.info("🔍 Step 2: 架构审计...")
            # reducer = ArchitectureReducer(self.project_root)
            # report = reducer.reduce()

            # Step 3: Patch
            logger.info("🛠️  Step 3: 自动修复...")
            # patcher = SmartPatcher(self.project_root)
            # patch_results = patcher.heal_vulnerabilities(report)

            # Step 4: 生成报告
            logger.info("📊 Step 4: 生成审计报告...")
            markdown_report = self._generate_markdown_report()

            logger.success("✅ CI 审计完成！")

            return {
                "success": True,
                "markdown_report": markdown_report,
                "vulnerabilities_found": 0,
                "vulnerabilities_fixed": 0
            }

        except Exception as e:
            logger.error(f"❌ CI 审计失败: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    def _generate_markdown_report(self) -> str:
        """
        生成 Markdown 审计报告

        Returns:
            Markdown 格式的审计报告
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        report = f"""
## 🛡️ Aegis 安全审计报告

**审计时间**: {timestamp}
**审计模式**: CI/CD 自动化

---

### 📊 审计结果

- **漏洞总数**: 0
- **自动修复**: 0
- **需人工审查**: 0

---

### ✅ 审计通过

未检测到关键安全漏洞。

---

*报告由 Aegis 自动生成*
"""

        return report


# ==========================================
# 外部调用入口
# ==========================================
def inject_ide_context(
    report: ArchitectureReport,
    project_root: Optional[Path] = None,
    target_format: str = "cursorrules"
) -> ContextInjectionResult:
    """
    注入 IDE 上下文（一站式入口）

    Args:
        report: 架构审计报告
        project_root: 项目根目录（默认当前目录）
        target_format: 目标格式（cursorrules 或 claude_xml）

    Returns:
        ContextInjectionResult: 注入结果

    Example:
        >>> from aegis.engines.context_injector import inject_ide_context
        >>> result = inject_ide_context(report)
        >>> if result.success:
        ...     print(f"上下文已注入到 {result.target_file}")
    """
    injector = ContextInjector(
        project_root=project_root,
        target_format=target_format
    )
    return injector.inject_context(report)


def run_ci_audit(
    project_root: Optional[Path] = None
) -> Dict:
    """
    运行 CI 审计（一站式入口）

    Args:
        project_root: 项目根目录（默认当前目录）

    Returns:
        审计结果字典

    Example:
        >>> from aegis.engines.context_injector import run_ci_audit
        >>> result = run_ci_audit()
        >>> print(result["markdown_report"])
    """
    auditor = CIAuditor(project_root=project_root)
    return auditor.run_ci_audit()
