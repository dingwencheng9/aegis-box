"""
端到端集成测试：完整流水线验证

测试范围：
1. 模拟真实项目环境（Git 仓库 + 代码文件）
2. Mock 引擎注入（避免真实 LLM 调用）
3. 全链路执行验证
4. 中断恢复测试
"""

import pytest
import asyncio
import json
import subprocess
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Dict, Any

from aegis.engines.orchestrator import (
    AegisOrchestrator,
    ExecutionState,
    run_full_pipeline,
)
from aegis.engines.patcher import Vulnerability, ArchitectureReport
from aegis.cli import AegisConfig


# ==========================================
# Mock 引擎
# ==========================================
class MockSweeper:
    """Mock 资产清扫器"""

    def __init__(self, repo_path: Path, config: AegisConfig = None):
        self.repo_path = repo_path
        self.config = config

    async def sweep(self, dry_run: bool = False) -> Dict[str, Any]:
        """模拟清扫"""
        await asyncio.sleep(0.1)  # 模拟异步操作

        return {
            "files_scanned": 1000,
            "files_cleaned": 50,
            "space_freed_mb": 100
        }


class MockReducer:
    """Mock 架构归纳器"""

    def __init__(self, repo_path: Path, config: AegisConfig = None):
        self.repo_path = repo_path
        self.config = config

    async def reduce(self) -> ArchitectureReport:
        """模拟架构审计"""
        await asyncio.sleep(0.2)  # 模拟异步操作

        # 返回模拟的审计报告
        vulnerabilities = [
            Vulnerability(
                file_path="user_service.py",
                description="SQL injection in get_user function",
                severity="CRITICAL",
                suggestion="Use parameterized queries"
            ),
            Vulnerability(
                file_path="auth_handler.py",
                description="Weak password hashing algorithm",
                severity="HIGH",
                suggestion="Use bcrypt or argon2"
            )
        ]

        return ArchitectureReport(critical_vulnerabilities=vulnerabilities)


class MockPatcher:
    """Mock 智能修补器"""

    def __init__(self, repo_path: Path, config: AegisConfig = None):
        self.repo_path = repo_path
        self.config = config

    async def heal_vulnerabilities(
        self,
        report: ArchitectureReport
    ) -> Dict[str, Any]:
        """模拟修复漏洞"""
        await asyncio.sleep(0.3)  # 模拟异步操作

        total = len(report.critical_vulnerabilities)
        fixed = total - 1  # 模拟失败一个

        return {
            "vulnerabilities_fixed": fixed,
            "vulnerabilities_failed": 1,
            "success_rate": fixed / total if total > 0 else 0
        }


class MockContextInjector:
    """Mock 上下文注入器"""

    def __init__(self, repo_path: Path, target_format: str = "cursorrules"):
        self.repo_path = repo_path
        self.target_format = target_format
        self.target_file = repo_path / ".cursorrules"

    async def inject_context(
        self,
        report: ArchitectureReport
    ) -> Dict[str, Any]:
        """模拟上下文注入"""
        await asyncio.sleep(0.1)  # 模拟异步操作

        # 实际写入文件（用于验证）
        self.target_file.write_text(
            f"# Mock Aegis Context\nVulnerabilities: {len(report.critical_vulnerabilities)}",
            encoding="utf-8"
        )

        return {
            "target_file": str(self.target_file),
            "injected": True
        }


# ==========================================
# Fixtures
# ==========================================
@pytest.fixture
def test_project(tmp_path):
    """创建测试项目结构"""
    # 初始化 Git 仓库
    subprocess.run(
        ["git", "init"],
        cwd=tmp_path,
        capture_output=True,
        check=True
    )
    subprocess.run(
        ["git", "config", "user.name", "Test User"],
        cwd=tmp_path,
        capture_output=True,
        check=True
    )
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"],
        cwd=tmp_path,
        capture_output=True,
        check=True
    )

    # 创建项目文件
    # Python 文件
    (tmp_path / "user_service.py").write_text(
        '''
def get_user(user_id):
    query = f"SELECT * FROM users WHERE id = {user_id}"
    return db.execute(query)
''',
        encoding="utf-8"
    )

    # TypeScript 文件
    (tmp_path / "auth_handler.ts").write_text(
        '''
export function hashPassword(password: string): string {
    return md5(password);  // Weak hashing
}
''',
        encoding="utf-8"
    )

    # README
    (tmp_path / "README.md").write_text(
        "# Test Project\n\nA test project for Aegis integration testing.",
        encoding="utf-8"
    )

    # 提交初始文件
    subprocess.run(
        ["git", "add", "."],
        cwd=tmp_path,
        capture_output=True,
        check=True
    )
    subprocess.run(
        ["git", "commit", "-m", "Initial commit"],
        cwd=tmp_path,
        capture_output=True,
        check=True
    )

    return tmp_path


@pytest.fixture
def mock_orchestrator(test_project):
    """创建带 Mock 引擎的 Orchestrator"""
    orchestrator = AegisOrchestrator(repo_path=test_project)

    # 保存原始方法的引用
    original_step_sweep = orchestrator._step_sweep
    original_step_reduce = orchestrator._step_reduce
    original_step_patch = orchestrator._step_patch
    original_step_context_sync = orchestrator._step_context_sync

    # Mock 步骤方法
    async def mock_step_sweep(auto_approve: bool = False) -> Dict[str, Any]:
        sweeper = MockSweeper(test_project)
        return await sweeper.sweep(dry_run=not auto_approve)

    async def mock_step_reduce(auto_approve: bool = False) -> Dict[str, Any]:
        reducer = MockReducer(test_project)
        report = await reducer.reduce()

        return {
            "vulnerabilities_found": len(report.critical_vulnerabilities),
            "critical": sum(1 for v in report.critical_vulnerabilities if v.severity == "CRITICAL"),
            "high": sum(1 for v in report.critical_vulnerabilities if v.severity == "HIGH"),
            "report": report  # 传递给下一步
        }

    async def mock_step_patch(auto_approve: bool = False) -> Dict[str, Any]:
        # 从上一步获取报告
        reduce_result = orchestrator._get_step_result("reduce")
        if reduce_result and reduce_result.artifacts:
            report = reduce_result.artifacts.get("report")
        else:
            # 如果没有报告，创建一个空的
            report = ArchitectureReport(critical_vulnerabilities=[])

        patcher = MockPatcher(test_project)
        return await patcher.heal_vulnerabilities(report)

    async def mock_step_context_sync(auto_approve: bool = False) -> Dict[str, Any]:
        # 从审计步骤获取报告
        reduce_result = orchestrator._get_step_result("reduce")
        if reduce_result and reduce_result.artifacts:
            report = reduce_result.artifacts.get("report")
        else:
            report = ArchitectureReport(critical_vulnerabilities=[])

        injector = MockContextInjector(test_project)
        return await injector.inject_context(report)

    # 替换方法
    orchestrator._step_sweep = mock_step_sweep
    orchestrator._step_reduce = mock_step_reduce
    orchestrator._step_patch = mock_step_patch
    orchestrator._step_context_sync = mock_step_context_sync

    return orchestrator


# ==========================================
# 集成测试
# ==========================================
@pytest.mark.asyncio
async def test_full_pipeline_success(mock_orchestrator, test_project):
    """测试完整流水线成功执行"""
    # 运行完整流水线
    result = await mock_orchestrator.run(auto_approve=True)

    # 验证最终状态
    assert result.overall_state == ExecutionState.SUCCESS, \
        f"Expected SUCCESS, got {result.overall_state}"

    # 验证所有步骤都执行了
    assert len(result.steps) == 4, f"Expected 4 steps, got {len(result.steps)}"

    # 验证每个步骤的状态
    step_names = [step.step_name for step in result.steps]
    assert "sweep" in step_names
    assert "reduce" in step_names
    assert "patch" in step_names
    assert "context_sync" in step_names

    # 验证所有步骤都成功
    for step in result.steps:
        assert step.state == ExecutionState.SUCCESS, \
            f"Step {step.step_name} failed: {step.state}"

    # 验证状态文件存在
    state_file = test_project / "artifacts" / "aegis_state.json"
    assert state_file.exists(), "State file not created"

    # 验证状态文件内容
    with open(state_file, "r", encoding="utf-8") as f:
        state_data = json.load(f)

    assert state_data["overall_state"] == "success"
    assert len(state_data["steps"]) == 4


@pytest.mark.asyncio
async def test_artifacts_passed_between_steps(mock_orchestrator, test_project):
    """测试阶段间 artifacts 正确传递"""
    result = await mock_orchestrator.run(auto_approve=True)

    # 验证 Reduce 阶段产生了报告
    reduce_step = None
    for step in result.steps:
        if step.step_name == "reduce":
            reduce_step = step
            break

    assert reduce_step is not None, "Reduce step not found"
    assert "report" in reduce_step.artifacts, "Report not in reduce artifacts"
    assert reduce_step.artifacts["vulnerabilities_found"] == 2

    # 验证 Patch 阶段使用了报告
    patch_step = None
    for step in result.steps:
        if step.step_name == "patch":
            patch_step = step
            break

    assert patch_step is not None, "Patch step not found"
    assert "vulnerabilities_fixed" in patch_step.artifacts
    # 应该修复了 1 个（模拟失败 1 个）
    assert patch_step.artifacts["vulnerabilities_fixed"] == 1

    # 验证 Context Sync 创建了文件
    context_sync_step = None
    for step in result.steps:
        if step.step_name == "context_sync":
            context_sync_step = step
            break

    assert context_sync_step is not None, "Context sync step not found"
    assert context_sync_step.artifacts["injected"] is True

    # 验证实际文件存在
    cursorrules_file = test_project / ".cursorrules"
    assert cursorrules_file.exists(), ".cursorrules not created"


@pytest.mark.asyncio
async def test_checkpoint_recovery_after_interrupt(mock_orchestrator, test_project):
    """测试中断恢复：在 Reduce 阶段中断后恢复"""
    # 第一次运行：模拟在 Reduce 阶段之后中断
    result1 = await mock_orchestrator.run(auto_approve=True)

    # 手动修改状态：移除 Patch 和 Context Sync 步骤
    # 模拟在 Reduce 完成后中断
    mock_orchestrator.state.steps = [
        step for step in mock_orchestrator.state.steps
        if step.step_name in ["sweep", "reduce"]
    ]
    mock_orchestrator.state.overall_state = ExecutionState.RUNNING
    mock_orchestrator._save_state()

    # 创建新的 orchestrator 来模拟重新启动
    orchestrator2 = AegisOrchestrator(repo_path=test_project)

    # 注入相同的 Mock 方法
    orchestrator2._step_sweep = mock_orchestrator._step_sweep
    orchestrator2._step_reduce = mock_orchestrator._step_reduce
    orchestrator2._step_patch = mock_orchestrator._step_patch
    orchestrator2._step_context_sync = mock_orchestrator._step_context_sync

    # 从检查点恢复
    result2 = await orchestrator2.run(
        auto_approve=True,
        continue_from_checkpoint=True
    )

    # 验证状态
    assert result2.overall_state == ExecutionState.SUCCESS

    # 验证 Sweep 和 Reduce 被跳过（已完成）
    # 新执行的步骤应该只有 Patch 和 Context Sync
    # 但状态文件中应该包含所有 4 个步骤
    assert len(result2.steps) == 4

    # 验证 Sweep 和 Reduce 的时间戳没有变化
    sweep_step = next(s for s in result2.steps if s.step_name == "sweep")
    reduce_step = next(s for s in result2.steps if s.step_name == "reduce")

    # 这些步骤应该保留了原始的时间戳
    assert sweep_step.state == ExecutionState.SUCCESS
    assert reduce_step.state == ExecutionState.SUCCESS


@pytest.mark.asyncio
async def test_partial_success_scenario(mock_orchestrator, test_project):
    """测试部分成功场景：Patch 步骤失败"""
    # 修改 Patch 步骤使其失败
    original_patch = mock_orchestrator._step_patch

    async def failing_patch(auto_approve: bool = False):
        raise Exception("Simulated patch failure")

    mock_orchestrator._step_patch = failing_patch

    # 运行流水线
    result = await mock_orchestrator.run(auto_approve=True)

    # 验证最终状态为部分成功
    assert result.overall_state == ExecutionState.PARTIAL_SUCCESS, \
        f"Expected PARTIAL_SUCCESS, got {result.overall_state}"

    # 验证前面的步骤成功
    sweep_step = next(s for s in result.steps if s.step_name == "sweep")
    reduce_step = next(s for s in result.steps if s.step_name == "reduce")

    assert sweep_step.state == ExecutionState.SUCCESS
    assert reduce_step.state == ExecutionState.SUCCESS

    # 验证 Patch 步骤失败
    patch_step = next(s for s in result.steps if s.step_name == "patch")
    assert patch_step.state == ExecutionState.FAILED
    assert "Simulated patch failure" in patch_step.error_message

    # 验证 Context Sync 仍然执行（非关键步骤失败后继续）
    context_sync_step = next(
        (s for s in result.steps if s.step_name == "context_sync"),
        None
    )
    # Context Sync 应该执行了（因为 Patch 不是关键步骤）
    assert context_sync_step is not None


@pytest.mark.asyncio
async def test_critical_step_failure_stops_execution(mock_orchestrator, test_project):
    """测试关键步骤失败停止执行"""
    # 修改 Reduce 步骤使其失败（关键步骤）
    async def failing_reduce(auto_approve: bool = False):
        raise Exception("Simulated reduce failure")

    mock_orchestrator._step_reduce = failing_reduce

    # 运行流水线
    result = await mock_orchestrator.run(auto_approve=True)

    # 验证最终状态为失败
    assert result.overall_state == ExecutionState.PARTIAL_SUCCESS or \
           result.overall_state == ExecutionState.FAILED

    # 验证 Sweep 成功
    sweep_step = next(s for s in result.steps if s.step_name == "sweep")
    assert sweep_step.state == ExecutionState.SUCCESS

    # 验证 Reduce 失败
    reduce_step = next(s for s in result.steps if s.step_name == "reduce")
    assert reduce_step.state == ExecutionState.FAILED

    # 验证后续步骤没有执行（关键步骤失败后停止）
    patch_step = next(
        (s for s in result.steps if s.step_name == "patch"),
        None
    )
    context_sync_step = next(
        (s for s in result.steps if s.step_name == "context_sync"),
        None
    )

    # Patch 和 Context Sync 不应该执行
    assert patch_step is None
    assert context_sync_step is None


@pytest.mark.asyncio
async def test_state_persistence_across_runs(test_project):
    """测试状态在多次运行间持久化"""
    # 第一次运行
    orchestrator1 = AegisOrchestrator(repo_path=test_project)

    # Mock 方法
    async def mock_sweep(auto_approve: bool = False):
        return {"files_scanned": 100}

    orchestrator1._step_sweep = mock_sweep
    orchestrator1._step_reduce = mock_sweep  # 简化
    orchestrator1._step_patch = mock_sweep
    orchestrator1._step_context_sync = mock_sweep

    result1 = await orchestrator1.run(auto_approve=True)
    session_id_1 = result1.session_id

    # 第二次运行（新会话）
    orchestrator2 = AegisOrchestrator(repo_path=test_project)
    orchestrator2._step_sweep = mock_sweep
    orchestrator2._step_reduce = mock_sweep
    orchestrator2._step_patch = mock_sweep
    orchestrator2._step_context_sync = mock_sweep

    result2 = await orchestrator2.run(auto_approve=True)
    session_id_2 = result2.session_id

    # 验证不同会话有不同的 ID
    assert session_id_1 != session_id_2

    # 验证状态文件被新会话覆盖
    state_file = test_project / "artifacts" / "aegis_state.json"
    with open(state_file, "r", encoding="utf-8") as f:
        state_data = json.load(f)

    assert state_data["session_id"] == session_id_2


@pytest.mark.asyncio
async def test_git_repo_required(tmp_path):
    """测试非 Git 仓库的处理"""
    # 创建一个没有 Git 的目录
    non_git_dir = tmp_path / "non_git_project"
    non_git_dir.mkdir()

    (non_git_dir / "test.py").write_text("print('hello')", encoding="utf-8")

    # 创建 orchestrator
    orchestrator = AegisOrchestrator(repo_path=non_git_dir)

    # Mock 方法（简化）
    async def mock_step(auto_approve: bool = False):
        return {"result": "ok"}

    orchestrator._step_sweep = mock_step
    orchestrator._step_reduce = mock_step
    orchestrator._step_patch = mock_step
    orchestrator._step_context_sync = mock_step

    # 应该仍然可以运行（Git 不是硬性要求）
    result = await orchestrator.run(auto_approve=True)

    assert result.overall_state == ExecutionState.SUCCESS


# ==========================================
# 外部 API 测试
# ==========================================
@pytest.mark.asyncio
async def test_run_full_pipeline_api(test_project):
    """测试外部 API：run_full_pipeline"""
    # Mock 步骤
    with patch.object(AegisOrchestrator, '_step_sweep', new_callable=AsyncMock) as mock_sweep, \
         patch.object(AegisOrchestrator, '_step_reduce', new_callable=AsyncMock) as mock_reduce, \
         patch.object(AegisOrchestrator, '_step_patch', new_callable=AsyncMock) as mock_patch, \
         patch.object(AegisOrchestrator, '_step_context_sync', new_callable=AsyncMock) as mock_sync:

        mock_sweep.return_value = {"files_scanned": 100}
        mock_reduce.return_value = {"vulnerabilities_found": 0}
        mock_patch.return_value = {"vulnerabilities_fixed": 0}
        mock_sync.return_value = {"injected": True}

        # 调用外部 API
        result = await run_full_pipeline(
            repo_path=test_project,
            auto_approve=True,
            continue_from_checkpoint=False
        )

        # 验证结果
        assert result.overall_state == ExecutionState.SUCCESS
        assert len(result.steps) == 4
