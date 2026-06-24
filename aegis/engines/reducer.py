"""
🛡️ Aegis - Architecture Reducer (双轨架构归纳器)
Tier-1 并发文件分析 + Tier-2 架构总结
"""

import asyncio
from enum import Enum
from pathlib import Path
from typing import List, Optional, Dict
from datetime import datetime
from collections import defaultdict
from pydantic import BaseModel, Field
from loguru import logger

from aegis.core.llm import LLMClientFactory
from aegis.cli import AegisConfig
from aegis.engines.mapper import CodeSkeleton


# ==========================================
# 枚举类型
# ==========================================
class VulnerabilityLevel(str, Enum):
    """漏洞/代码异味严重级别"""
    P0 = "P0"  # 严重：安全漏洞、数据丢失风险
    P1 = "P1"  # 高：性能问题、架构缺陷
    P2 = "P2"  # 中：代码异味、可维护性问题


class AnalysisStatus(str, Enum):
    """分析状态"""
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"


# ==========================================
# Tier-1 输出：单文件摘要
# ==========================================
class VulnerabilityItem(BaseModel):
    """漏洞或代码异味项"""
    level: VulnerabilityLevel
    description: str
    location: Optional[str] = None  # 例如: "L45-L67"
    suggestion: Optional[str] = None  # 修复建议


class FileSummary(BaseModel):
    """
    单文件摘要（Tier-1 输出）

    职责：提供单个文件的核心信息和问题诊断
    """
    # 基础信息
    file_path: str = Field(..., description="文件路径")
    status: AnalysisStatus = Field(default=AnalysisStatus.SUCCESS, description="分析状态")

    # 核心摘要
    responsibility: str = Field(..., description="文件的主要职责（1-2 句话）")
    exposed_interfaces: List[str] = Field(
        default_factory=list,
        description="对外暴露的核心接口/类/函数（供其他模块调用）"
    )

    # 问题诊断
    vulnerabilities: List[VulnerabilityItem] = Field(
        default_factory=list,
        description="发现的漏洞和代码异味（按严重级别分类）"
    )

    # TODO 追踪
    priority_todos: List[str] = Field(
        default_factory=list,
        description="需要优先处理的 TODO/FIXME 项"
    )

    # 错误信息（如果分析失败）
    error_message: Optional[str] = Field(None, description="失败原因（status=FAILED 时）")

    @property
    def has_p0_issues(self) -> bool:
        """是否有 P0 级别问题"""
        return any(v.level == VulnerabilityLevel.P0 for v in self.vulnerabilities)

    @property
    def has_critical_todos(self) -> bool:
        """是否有关键 TODO"""
        return len(self.priority_todos) > 0


# ==========================================
# 中间聚合：项目全景视图
# ==========================================
class ProjectPanorama(BaseModel):
    """
    项目全景视图（聚合结果）

    职责：将所有 FileSummary 聚合为项目级别的统计和概览
    """
    # 统计信息
    total_files: int
    successful_files: int
    failed_files: int

    # 模块分组（按目录分组）
    modules: Dict[str, List[str]] = Field(
        default_factory=dict,
        description="模块名 -> 文件列表"
    )

    # 核心接口列表（去重）
    all_exposed_interfaces: List[str] = Field(
        default_factory=list,
        description="所有对外接口的汇总（已去重）"
    )

    # 问题汇总（降采样）
    p0_vulnerabilities: List[Dict] = Field(
        default_factory=list,
        description="所有 P0 级别问题（保留全部）"
    )
    p1_vulnerabilities: List[Dict] = Field(
        default_factory=list,
        description="所有 P1 级别问题（最多 30 个）"
    )
    p1_total_count: int = Field(default=0, description="P1 问题总数（含被截断的）")

    # TODO 汇总（降采样）
    all_todos: List[Dict] = Field(
        default_factory=list,
        description="所有优先 TODO 项（最多 50 个）"
    )
    todos_total_count: int = Field(default=0, description="TODO 总数（含被截断的）")


# ==========================================
# Tier-2 输出：架构报告
# ==========================================
class CouplingMetrics(BaseModel):
    """内聚与耦合度评价"""
    cohesion_score: int = Field(..., ge=0, le=100, description="内聚度评分 (0-100)")
    coupling_score: int = Field(..., ge=0, le=100, description="耦合度评分 (0-100)")
    evaluation: str = Field(..., description="评价说明")


class RefactoringAction(BaseModel):
    """可执行的重构建议"""
    priority: int = Field(..., ge=1, le=3, description="优先级 (1=最高)")
    title: str = Field(..., description="重构标题")
    reason: str = Field(..., description="为什么需要这个重构")
    action_steps: List[str] = Field(..., description="具体执行步骤")
    estimated_effort: str = Field(..., description="预估工作量（如 '2-3 天'）")


class ArchitectureReport(BaseModel):
    """
    架构报告（Tier-2 输出）

    职责：提供项目级别的架构评价和可执行建议
    """
    # 全局架构评价
    architecture_overview: str = Field(
        ...,
        description="系统架构总体评价（项目类型、架构模式、技术栈）"
    )

    architecture_patterns: List[str] = Field(
        default_factory=list,
        description="识别出的架构模式（如 MVC、DDD、微服务等）"
    )

    # 高危漏洞汇总
    critical_vulnerabilities: List[Dict] = Field(
        default_factory=list,
        description="P0 级别漏洞汇总（需要立即修复）"
    )

    # 内聚与耦合度
    coupling_metrics: CouplingMetrics = Field(
        ...,
        description="高内聚/低耦合度评价"
    )

    # Top 3 重构建议（Actionable）
    top_refactoring_actions: List[RefactoringAction] = Field(
        ...,
        description="Top 3 必须立刻执行的重构建议"
    )

    # 元数据
    analyzed_files: int = Field(..., description="分析的文件总数")
    generated_at: str = Field(..., description="报告生成时间")

    def to_markdown(self) -> str:
        """
        生成 Markdown 格式的报告

        Returns:
            Markdown 格式的完整架构报告
        """
        lines = []

        # 标题
        lines.append("# 🛡️ Aegis 架构审计报告\n")
        lines.append(f"**生成时间**: {self.generated_at}")
        lines.append(f"**分析文件数**: {self.analyzed_files}\n")

        # 架构概览
        lines.append("## 📊 架构概览\n")
        lines.append(self.architecture_overview + "\n")

        if self.architecture_patterns:
            lines.append("**识别的架构模式**:")
            for pattern in self.architecture_patterns:
                lines.append(f"- {pattern}")
            lines.append("")

        # 内聚与耦合度
        lines.append("## 🔗 内聚与耦合度评价\n")
        lines.append(f"- **内聚度**: {self.coupling_metrics.cohesion_score}/100")
        lines.append(f"- **耦合度**: {self.coupling_metrics.coupling_score}/100")
        lines.append(f"- **评价**: {self.coupling_metrics.evaluation}\n")

        # 高危漏洞
        if self.critical_vulnerabilities:
            lines.append("## 🚨 高危漏洞（P0）\n")
            for i, vuln in enumerate(self.critical_vulnerabilities, 1):
                lines.append(f"### {i}. {vuln.get('file', 'Unknown')}")
                lines.append(f"**描述**: {vuln.get('description', 'N/A')}")
                if vuln.get('location'):
                    lines.append(f"**位置**: {vuln['location']}")
                if vuln.get('suggestion'):
                    lines.append(f"**建议**: {vuln['suggestion']}")
                lines.append("")

        # Top 3 重构建议
        lines.append("## 🔧 Top 3 重构建议\n")
        for action in self.top_refactoring_actions:
            lines.append(f"### {action.priority}. {action.title}")
            lines.append(f"**原因**: {action.reason}")
            lines.append(f"**预估工作量**: {action.estimated_effort}\n")
            lines.append("**执行步骤**:")
            for j, step in enumerate(action.action_steps, 1):
                lines.append(f"{j}. {step}")
            lines.append("")

        return "\n".join(lines)


# ==========================================
# 双轨架构归纳器
# ==========================================
class ArchitectureReducer:
    """
    双轨架构归纳器

    职责：
    1. Tier-1 并发分析所有文件（带背压控制）
    2. 聚合为项目全景视图（带降采样）
    3. Tier-2 生成架构报告
    4. 持久化到磁盘
    """

    def __init__(
        self,
        config: AegisConfig,
        max_concurrent: int = 50,  # 并发背压控制
    ):
        """
        初始化归纳器

        Args:
            config: Aegis 全局配置
            max_concurrent: 最大并发数（防止资源耗尽）
        """
        self.config = config
        self.max_concurrent = max_concurrent

        # 创建 LLM 客户端
        factory = LLMClientFactory(config)
        self.tier1_client = factory.create_tier1_client()
        self.tier2_client = factory.create_tier2_client()

        # 并发控制
        self.semaphore = asyncio.Semaphore(max_concurrent)

        logger.info(f"ArchitectureReducer 初始化完成 (max_concurrent={max_concurrent})")

    async def analyze_file(
        self,
        skeleton: CodeSkeleton
    ) -> FileSummary:
        """
        Tier-1: 分析单个文件（带并发控制和容错）

        Args:
            skeleton: 代码骨架

        Returns:
            FileSummary: 文件摘要（失败时返回 FAILED 状态）
        """
        async with self.semaphore:  # 并发背压控制
            # 🆕 文件级重试装甲（3 次重试 + 指数退避）
            max_file_retries = 3
            base_delay = 2.0  # 初始等待 2 秒

            for retry_attempt in range(max_file_retries):
                try:
                    # 构建 Prompt
                    prompt = self._build_file_analysis_prompt(skeleton)

                    # 调用 Tier-1 模型
                    summary = await self.tier1_client.chat(
                        prompt=prompt,
                        response_model=FileSummary,
                        system_prompt="你是一个代码审查专家，专注于发现潜在问题和架构缺陷",
                        temperature=0.3,
                        max_tokens=4096,  # 增加到 4096 以避免复杂文件被截断
                    )

                    logger.success(f"✅ 分析成功: {skeleton.file_path}")

                    # 兼容部分未返回路径的模型：强制设置 file_path
                    summary.file_path = str(skeleton.file_path)
                    return summary

                except Exception as e:
                    error_str = str(e).lower()
                    # 判断是否为空响应或网络错误（值得重试）
                    is_retriable_error = any(pattern in error_str for pattern in [
                        'eof while parsing',  # 空响应
                        'empty',  # 空内容
                        'timeout',  # 超时
                        'connection',  # 连接问题
                        'nodename nor servname',  # DNS 错误
                    ])

                    if is_retriable_error and retry_attempt < max_file_retries - 1:
                        wait_time = base_delay * (2 ** retry_attempt)  # 指数退避: 2s, 4s, 8s
                        logger.warning(
                            f"⚠️ 文件分析失败（第 {retry_attempt + 1}/{max_file_retries} 次）: "
                            f"{skeleton.file_path} - {e}"
                        )
                        logger.info(f"⏳ 等待 {wait_time:.1f}s 后重试...")
                        await asyncio.sleep(wait_time)
                        continue
                    else:
                        # 最后一次重试失败，或不可重试错误
                        logger.error(f"❌ 分析失败（已耗尽重试）: {skeleton.file_path} - {e}")
                        return FileSummary(
                            file_path=str(skeleton.file_path),
                            status=AnalysisStatus.FAILED,
                            responsibility="分析失败",
                            error_message=str(e)
                        )

            # 理论上不会到这里（for-else 保护）
            return FileSummary(
                file_path=str(skeleton.file_path),
                status=AnalysisStatus.FAILED,
                responsibility="分析失败",
                error_message="重试耗尽"
            )

    async def analyze_project(
        self,
        skeletons: List[CodeSkeleton]
    ) -> ArchitectureReport:
        """
        完整的双轨分析流程

        Args:
            skeletons: 代码骨架列表

        Returns:
            ArchitectureReport: 架构报告
        """
        logger.info(f"🚀 启动双轨架构分析: {len(skeletons)} 个文件")

        # Step 1: Tier-1 并发分析所有文件
        logger.info("Step 1: Tier-1 并发文件分析...")
        tasks = [self.analyze_file(skeleton) for skeleton in skeletons]
        summaries = await asyncio.gather(*tasks)

        # 统计成功/失败
        successful = [s for s in summaries if s.status == AnalysisStatus.SUCCESS]
        failed = [s for s in summaries if s.status == AnalysisStatus.FAILED]
        logger.info(f"  - 成功: {len(successful)}/{len(skeletons)}")
        logger.info(f"  - 失败: {len(failed)}/{len(skeletons)}")

        # Step 2: 聚合全景视图
        logger.info("Step 2: 聚合项目全景视图...")
        panorama = self._aggregate_panorama(summaries)

        # Step 3: Tier-2 架构总结
        logger.info("Step 3: Tier-2 架构总结...")
        report = await self._generate_architecture_report(panorama)

        # Step 4: 持久化报告
        logger.info("Step 4: 持久化报告...")
        self._save_report(report)

        logger.success("🎉 架构分析完成！")
        return report

    def _aggregate_panorama(
        self,
        summaries: List[FileSummary]
    ) -> ProjectPanorama:
        """
        聚合项目全景视图（带降采样防止上下文爆炸）

        Args:
            summaries: 所有文件摘要

        Returns:
            ProjectPanorama: 全景视图
        """
        # 统计信息
        total = len(summaries)
        successful = sum(1 for s in summaries if s.status == AnalysisStatus.SUCCESS)
        failed = total - successful

        # 模块分组（按目录分组）
        modules = defaultdict(list)
        for summary in summaries:
            if summary.status == AnalysisStatus.SUCCESS:
                # 提取目录名作为模块名
                file_path = Path(summary.file_path)
                module_name = file_path.parent.name or "root"
                modules[module_name].append(summary.file_path)

        # 核心接口列表（去重）
        all_interfaces = set()
        for summary in summaries:
            if summary.status == AnalysisStatus.SUCCESS:
                all_interfaces.update(summary.exposed_interfaces)

        # 问题汇总（降采样）
        p0_vulns = []
        p1_vulns = []

        for summary in summaries:
            if summary.status == AnalysisStatus.SUCCESS:
                for vuln in summary.vulnerabilities:
                    vuln_dict = {
                        "file": summary.file_path,
                        "level": vuln.level.value,
                        "description": vuln.description,
                        "location": vuln.location,
                        "suggestion": vuln.suggestion,
                    }

                    if vuln.level == VulnerabilityLevel.P0:
                        p0_vulns.append(vuln_dict)  # P0 保留全部
                    elif vuln.level == VulnerabilityLevel.P1:
                        p1_vulns.append(vuln_dict)

        # P1 降采样：最多保留 30 个
        p1_total_count = len(p1_vulns)
        if len(p1_vulns) > 30:
            logger.warning(f"P1 问题过多 ({len(p1_vulns)})，降采样至 30 个")
            p1_vulns = p1_vulns[:30]

        # TODO 汇总（降采样）
        all_todos = []
        for summary in summaries:
            if summary.status == AnalysisStatus.SUCCESS:
                for todo in summary.priority_todos:
                    all_todos.append({
                        "file": summary.file_path,
                        "todo": todo
                    })

        # TODO 降采样：最多保留 50 个
        todos_total_count = len(all_todos)
        if len(all_todos) > 50:
            logger.warning(f"TODO 过多 ({len(all_todos)})，降采样至 50 个")
            all_todos = all_todos[:50]

        return ProjectPanorama(
            total_files=total,
            successful_files=successful,
            failed_files=failed,
            modules=dict(modules),
            all_exposed_interfaces=sorted(list(all_interfaces)),
            p0_vulnerabilities=p0_vulns,
            p1_vulnerabilities=p1_vulns,
            p1_total_count=p1_total_count,
            all_todos=all_todos,
            todos_total_count=todos_total_count,
        )

    async def _generate_architecture_report(
        self,
        panorama: ProjectPanorama
    ) -> ArchitectureReport:
        """
        Tier-2: 生成架构报告

        Args:
            panorama: 项目全景视图

        Returns:
            ArchitectureReport: 架构报告
        """
        # 构建 Tier-2 Prompt
        prompt = self._build_architecture_prompt(panorama)

        # 调用 Tier-2 模型
        report = await self.tier2_client.chat(
            prompt=prompt,
            response_model=ArchitectureReport,
            system_prompt="你是一个资深软件架构师，擅长系统性分析和提供可执行建议",
            temperature=0.5,
            max_tokens=4096,
        )

        # 填充元数据
        report.analyzed_files = panorama.total_files
        report.generated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        return report

    def _save_report(self, report: ArchitectureReport):
        """
        持久化报告到磁盘

        Args:
            report: 架构报告
        """
        # 创建目录
        report_dir = Path.cwd() / ".aegis" / "reports"
        report_dir.mkdir(parents=True, exist_ok=True)

        # 保存 Markdown
        report_path = report_dir / "architecture_report.md"
        report_path.write_text(report.to_markdown(), encoding="utf-8")

        logger.success(f"📄 报告已保存: {report_path}")

    def _build_file_analysis_prompt(self, skeleton: CodeSkeleton) -> str:
        """
        构建 Tier-1 Prompt（强调跨函数引用分析）

        Args:
            skeleton: 代码骨架

        Returns:
            Prompt 字符串
        """
        # 提取函数调用关系（护城河）- 使用防御性编程
        call_relationships = []

        # 提取函数调用关系
        if hasattr(skeleton, 'functions'):
            for func in skeleton.functions:
                if getattr(func, 'calls', None):
                    call_relationships.append(
                        f"  - `{func.name}` 调用: {', '.join(list(func.calls)[:5])}"
                    )

        if hasattr(skeleton, 'classes'):
            for cls in skeleton.classes:
                for method in getattr(cls, 'methods', []):
                    if getattr(method, 'calls', None):
                        call_relationships.append(
                            f"  - `{cls.name}.{method.name}` 调用: {', '.join(list(method.calls)[:5])}"
                        )

        calls_section = "\n".join(call_relationships) if call_relationships else "  （无明显的跨函数调用）"

        # 安全获取 language 值
        language_val = skeleton.language.value if hasattr(skeleton.language, 'value') else str(skeleton.language)

        prompt = f"""
请分析以下代码骨架（Skeleton），并提供详细的文件摘要。

## 文件信息
**路径**: {skeleton.file_path}
**原始行数**: {getattr(skeleton, 'total_lines', 'Unknown')}
**语言**: {language_val}

## 代码骨架
```
{skeleton.to_markdown()}
```

## 🔍 关键：跨函数调用关系（Aegis 护城河）
请特别关注以下函数调用关系，用于发现架构层面的高耦合和潜在死代码：

{calls_section}

## 分析要求
请严格提取该文件的职责、暴露接口、漏洞（P0/P1/P2）和重点TODO项。

### 重点关注
- 通过 **跨函数调用关系** 发现高耦合（一个函数调用过多其他函数）
- 通过调用关系发现潜在的死代码（定义了但从未被调用）
- SQL 注入、XSS、硬编码密钥等安全问题（P0）
- 性能瓶颈、N+1 查询、缺少索引（P1）
- 代码异味、过长函数、深层嵌套（P2）
"""

        return prompt.strip()

    def _build_architecture_prompt(self, panorama: ProjectPanorama) -> str:
        """
        构建 Tier-2 Prompt

        Args:
            panorama: 项目全景视图

        Returns:
            Prompt 字符串
        """
        # 构建模块列表
        modules_list = "\n".join([
            f"- **{module}**: {len(files)} 个文件"
            for module, files in panorama.modules.items()
        ])

        # 构建 P0 漏洞列表
        p0_list = ""
        if panorama.p0_vulnerabilities:
            p0_items = []
            for vuln in panorama.p0_vulnerabilities[:10]:  # 最多显示 10 个
                p0_items.append(f"  - {vuln['file']}: {vuln['description']}")
            p0_list = "\n".join(p0_items)
        else:
            p0_list = "  （未发现 P0 级别漏洞）"

        # 构建 P1 统计
        p1_summary = f"发现 {panorama.p1_total_count} 个 P1 问题"
        if panorama.p1_total_count > 30:
            p1_summary += f"（已降采样至 30 个）"

        prompt = f"""
你是一个资深软件架构师。请基于以下项目全景视图，生成一份完整的架构审计报告。

## 项目统计
- **总文件数**: {panorama.total_files}
- **成功分析**: {panorama.successful_files}
- **失败**: {panorama.failed_files}

## 模块结构
{modules_list}

## 对外接口（已去重）
共 {len(panorama.all_exposed_interfaces)} 个核心接口（部分示例）:
{", ".join(panorama.all_exposed_interfaces[:20])}

## 高危漏洞（P0）
{p0_list}

## 架构问题（P1）
{p1_summary}

## TODO 追踪
共 {panorama.todos_total_count} 个 TODO 项

## 分析要求
请按照以下 JSON Schema 格式输出：

1. **architecture_overview** (str): 系统架构总体评价
   - 项目类型（Web后端/前端/CLI/库）
   - 架构模式（MVC/DDD/微服务/单体）
   - 技术栈概述

2. **architecture_patterns** (List[str]): 识别出的架构模式

3. **critical_vulnerabilities** (List[dict]): P0 级别漏洞汇总
   - file, description, location, suggestion

4. **coupling_metrics** (dict): 内聚与耦合度评价
   - cohesion_score (0-100): 内聚度评分
   - coupling_score (0-100): 耦合度评分
   - evaluation: 评价说明

5. **top_refactoring_actions** (List): Top 3 重构建议（可执行）
   - priority (1-3): 优先级
   - title: 重构标题
   - reason: 为什么需要这个重构
   - action_steps: 具体执行步骤（List[str]）
   - estimated_effort: 预估工作量（如 "2-3 天"）

### 重点要求
- 必须包含具体的 `cohesion_score` 和 `coupling_score`
- 重构建议必须是 **可执行的**，包含具体步骤
- 架构模式识别要准确（不要臆测）
"""

        return prompt.strip()


# ==========================================
# 外部调用入口
# ==========================================
async def reduce_architecture(
    config: AegisConfig,
    skeletons: List[CodeSkeleton],
    max_concurrent: int = 50
) -> ArchitectureReport:
    """
    架构归纳的外部调用入口

    Args:
        config: Aegis 配置
        skeletons: 代码骨架列表
        max_concurrent: 最大并发数

    Returns:
        ArchitectureReport: 架构报告
    """
    reducer = ArchitectureReducer(config, max_concurrent=max_concurrent)
    report = await reducer.analyze_project(skeletons)
    return report
