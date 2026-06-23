"""
测试 Architecture Reducer 的核心功能
"""

import pytest
import asyncio
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

from aegis.engines.reducer import (
    ArchitectureReducer,
    FileSummary,
    VulnerabilityItem,
    VulnerabilityLevel,
    AnalysisStatus,
    ProjectPanorama,
    ArchitectureReport,
    CouplingMetrics,
    RefactoringAction,
)
from aegis.engines.mapper import CodeSkeleton, Language, FunctionInfo
from aegis.cli import AegisConfig


# ==========================================
# Fixtures
# ==========================================
@pytest.fixture
def mock_config():
    """Mock AegisConfig"""
    return AegisConfig()


@pytest.fixture
def sample_skeleton():
    """创建测试用的 CodeSkeleton"""
    func = FunctionInfo(
        name="get_user",
        line_start=10,
        line_end=20,
        signature="def get_user(user_id: int):",
        calls={"fetch_from_db", "validate_user"}
    )

    skeleton = CodeSkeleton(
        file_path=Path("test_service.py"),
        language=Language.PYTHON,
        total_lines=100,
        skeleton_lines=20,
        compression_ratio=0.2,
        functions=[func]
    )

    return skeleton


@pytest.fixture
def sample_file_summary():
    """创建测试用的 FileSummary"""
    return FileSummary(
        file_path="test_service.py",
        status=AnalysisStatus.SUCCESS,
        responsibility="用户服务，负责用户信息的 CRUD 操作",
        exposed_interfaces=["get_user", "create_user"],
        vulnerabilities=[
            VulnerabilityItem(
                level=VulnerabilityLevel.P0,
                description="SQL 注入风险",
                location="L45",
                suggestion="使用参数化查询"
            )
        ],
        priority_todos=["添加缓存机制"]
    )


# ==========================================
# Pydantic 模型测试
# ==========================================
def test_vulnerability_item():
    """测试 VulnerabilityItem 模型"""
    vuln = VulnerabilityItem(
        level=VulnerabilityLevel.P0,
        description="SQL 注入",
        location="L45",
        suggestion="使用参数化查询"
    )

    assert vuln.level == VulnerabilityLevel.P0
    assert vuln.description == "SQL 注入"


def test_file_summary_properties(sample_file_summary):
    """测试 FileSummary 的属性"""
    assert sample_file_summary.has_p0_issues is True
    assert sample_file_summary.has_critical_todos is True
    assert sample_file_summary.status == AnalysisStatus.SUCCESS


def test_file_summary_failed():
    """测试失败的 FileSummary"""
    failed_summary = FileSummary(
        file_path="broken.py",
        status=AnalysisStatus.FAILED,
        responsibility="分析失败",
        error_message="Timeout"
    )

    assert failed_summary.status == AnalysisStatus.FAILED
    assert failed_summary.error_message == "Timeout"
    assert failed_summary.has_p0_issues is False


def test_architecture_report_to_markdown():
    """测试 ArchitectureReport 的 to_markdown 方法"""
    report = ArchitectureReport(
        architecture_overview="这是一个 Web 后端项目",
        architecture_patterns=["MVC", "RESTful API"],
        critical_vulnerabilities=[
            {"file": "user.py", "description": "SQL 注入", "location": "L45"}
        ],
        coupling_metrics=CouplingMetrics(
            cohesion_score=75,
            coupling_score=30,
            evaluation="内聚度良好，耦合度偏高"
        ),
        top_refactoring_actions=[
            RefactoringAction(
                priority=1,
                title="拆分用户服务",
                reason="文件过大，职责不清",
                action_steps=["拆分为 user_query.py", "拆分为 user_command.py"],
                estimated_effort="2-3 天"
            )
        ],
        analyzed_files=100,
        generated_at="2026-06-23 14:00:00"
    )

    markdown = report.to_markdown()

    assert "# 🛡️ Aegis 架构审计报告" in markdown
    assert "Web 后端项目" in markdown
    assert "MVC" in markdown
    assert "SQL 注入" in markdown
    assert "拆分用户服务" in markdown


# ==========================================
# ArchitectureReducer 测试
# ==========================================
@pytest.mark.asyncio
async def test_reducer_initialization(mock_config):
    """测试 Reducer 初始化"""
    reducer = ArchitectureReducer(mock_config, max_concurrent=10)

    assert reducer.max_concurrent == 10
    assert reducer.semaphore._value == 10
    assert reducer.tier1_client is not None
    assert reducer.tier2_client is not None


@pytest.mark.asyncio
async def test_analyze_file_success(mock_config, sample_skeleton):
    """测试单文件分析（成功）"""
    reducer = ArchitectureReducer(mock_config)

    # Mock LLM 客户端
    mock_summary = FileSummary(
        file_path=str(sample_skeleton.file_path),
        responsibility="测试服务",
        exposed_interfaces=["test_func"],
    )

    reducer.tier1_client.chat = AsyncMock(return_value=mock_summary)

    # 执行分析
    result = await reducer.analyze_file(sample_skeleton)

    assert result.status == AnalysisStatus.SUCCESS
    assert result.file_path == str(sample_skeleton.file_path)
    assert result.responsibility == "测试服务"


@pytest.mark.asyncio
async def test_analyze_file_failure(mock_config, sample_skeleton):
    """测试单文件分析（失败容错）"""
    reducer = ArchitectureReducer(mock_config)

    # Mock LLM 客户端抛出异常
    reducer.tier1_client.chat = AsyncMock(side_effect=Exception("Network error"))

    # 执行分析（应该返回 FAILED 而不是抛出异常）
    result = await reducer.analyze_file(sample_skeleton)

    assert result.status == AnalysisStatus.FAILED
    assert result.responsibility == "分析失败"
    assert "Network error" in result.error_message


def test_aggregate_panorama(mock_config):
    """测试全景视图聚合"""
    reducer = ArchitectureReducer(mock_config)

    # 创建测试数据
    summaries = [
        FileSummary(
            file_path="api/user.py",
            responsibility="用户 API",
            exposed_interfaces=["get_user", "create_user"],
            vulnerabilities=[
                VulnerabilityItem(
                    level=VulnerabilityLevel.P0,
                    description="SQL 注入"
                )
            ]
        ),
        FileSummary(
            file_path="api/post.py",
            responsibility="帖子 API",
            exposed_interfaces=["get_post", "create_user"],  # 重复接口
            vulnerabilities=[
                VulnerabilityItem(
                    level=VulnerabilityLevel.P1,
                    description="性能问题"
                )
            ]
        ),
        FileSummary(
            file_path="broken.py",
            status=AnalysisStatus.FAILED,
            responsibility="分析失败"
        )
    ]

    # 聚合
    panorama = reducer._aggregate_panorama(summaries)

    # 验证统计
    assert panorama.total_files == 3
    assert panorama.successful_files == 2
    assert panorama.failed_files == 1

    # 验证模块分组
    assert "api" in panorama.modules
    assert len(panorama.modules["api"]) == 2

    # 验证接口去重
    assert "get_user" in panorama.all_exposed_interfaces
    assert "create_user" in panorama.all_exposed_interfaces
    assert len([x for x in panorama.all_exposed_interfaces if x == "create_user"]) == 1  # 去重

    # 验证漏洞分类
    assert len(panorama.p0_vulnerabilities) == 1
    assert len(panorama.p1_vulnerabilities) == 1


def test_aggregate_panorama_sampling(mock_config):
    """测试降采样（防止上下文爆炸）"""
    reducer = ArchitectureReducer(mock_config)

    # 创建大量 P1 问题
    summaries = []
    for i in range(50):
        summaries.append(
            FileSummary(
                file_path=f"file_{i}.py",
                responsibility="测试",
                vulnerabilities=[
                    VulnerabilityItem(
                        level=VulnerabilityLevel.P1,
                        description=f"问题 {i}"
                    )
                ]
            )
        )

    panorama = reducer._aggregate_panorama(summaries)

    # 验证 P1 降采样（最多 30 个）
    assert len(panorama.p1_vulnerabilities) == 30
    assert panorama.p1_total_count == 50  # 记录总数


def test_build_file_analysis_prompt(mock_config, sample_skeleton):
    """测试 Tier-1 Prompt 构建"""
    reducer = ArchitectureReducer(mock_config)

    prompt = reducer._build_file_analysis_prompt(sample_skeleton)

    # 验证 Prompt 包含关键信息
    assert "test_service.py" in prompt
    assert "跨函数调用关系" in prompt  # 护城河
    assert "fetch_from_db" in prompt  # 函数调用
    assert "validate_user" in prompt
    assert "responsibility" in prompt
    assert "vulnerabilities" in prompt


def test_build_architecture_prompt(mock_config):
    """测试 Tier-2 Prompt 构建"""
    reducer = ArchitectureReducer(mock_config)

    panorama = ProjectPanorama(
        total_files=100,
        successful_files=95,
        failed_files=5,
        modules={"api": ["user.py", "post.py"]},
        all_exposed_interfaces=["get_user", "create_user"],
        p0_vulnerabilities=[{"file": "user.py", "description": "SQL 注入"}],
        p1_vulnerabilities=[],
        p1_total_count=0,
        all_todos=[],
        todos_total_count=0
    )

    prompt = reducer._build_architecture_prompt(panorama)

    # 验证 Prompt 包含关键信息
    assert "100" in prompt  # 总文件数
    assert "95" in prompt   # 成功数
    assert "api" in prompt  # 模块名
    assert "SQL 注入" in prompt
    assert "architecture_overview" in prompt
    assert "top_refactoring_actions" in prompt


def test_save_report(mock_config, tmp_path, monkeypatch):
    """测试报告持久化"""
    # 修改当前工作目录为临时目录
    monkeypatch.chdir(tmp_path)

    reducer = ArchitectureReducer(mock_config)

    report = ArchitectureReport(
        architecture_overview="测试项目",
        architecture_patterns=["MVC"],
        critical_vulnerabilities=[],
        coupling_metrics=CouplingMetrics(
            cohesion_score=80,
            coupling_score=20,
            evaluation="良好"
        ),
        top_refactoring_actions=[],
        analyzed_files=10,
        generated_at="2026-06-23"
    )

    # 保存报告
    reducer._save_report(report)

    # 验证文件存在
    report_path = tmp_path / ".aegis" / "reports" / "architecture_report.md"
    assert report_path.exists()

    # 验证内容
    content = report_path.read_text()
    assert "测试项目" in content
    assert "MVC" in content
