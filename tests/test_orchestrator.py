"""
测试 Orchestrator 的核心功能
"""

import pytest
import asyncio
import json
from pathlib import Path
from unittest.mock import MagicMock, patch, AsyncMock

from aegis.engines.orchestrator import (
    AegisOrchestrator,
    ExecutionState,
    StepResult,
    OrchestratorState,
    run_full_pipeline,
)


# ==========================================
# Fixtures
# ==========================================
@pytest.fixture
def temp_orchestrator(tmp_path):
    """临时 Orchestrator"""
    orchestrator = AegisOrchestrator(repo_path=tmp_path)
    return orchestrator


# ==========================================
# OrchestratorState 测试
# ==========================================
def test_step_result_creation():
    """测试 StepResult 创建"""
    result = StepResult(
        step_name="sweep",
        state=ExecutionState.SUCCESS,
        start_time="2026-06-23T10:00:00"
    )

    assert result.step_name == "sweep"
    assert result.state == ExecutionState.SUCCESS
    assert result.artifacts == {}


def test_orchestrator_state_to_dict():
    """测试状态序列化"""
    state = OrchestratorState(
        session_id="test-001",
        start_time="2026-06-23T10:00:00",
        end_time="2026-06-23T11:00:00",
        steps=[
            StepResult(
                step_name="sweep",
                state=ExecutionState.SUCCESS,
                start_time="2026-06-23T10:00:00"
            )
        ],
        overall_state=ExecutionState.SUCCESS,
        summary={"total_steps": 1}
    )

    data = state.to_dict()

    assert data["session_id"] == "test-001"
    assert len(data["steps"]) == 1
    assert data["overall_state"] == "success"


def test_orchestrator_state_from_dict():
    """测试状态反序列化"""
    data = {
        "session_id": "test-001",
        "start_time": "2026-06-23T10:00:00",
        "end_time": "2026-06-23T11:00:00",
        "steps": [
            {
                "step_name": "sweep",
                "state": "success",
                "start_time": "2026-06-23T10:00:00",
                "end_time": "2026-06-23T10:05:00",
                "error_message": None,
                "artifacts": {"files_scanned": 100}
            }
        ],
        "overall_state": "success",
        "summary": {"total_steps": 1}
    }

    state = OrchestratorState.from_dict(data)

    assert state.session_id == "test-001"
    assert len(state.steps) == 1
    assert state.steps[0].step_name == "sweep"
    assert state.steps[0].state == ExecutionState.SUCCESS


# ==========================================
# AegisOrchestrator 测试
# ==========================================
def test_orchestrator_initialization(temp_orchestrator):
    """测试 Orchestrator 初始化"""
    assert temp_orchestrator.repo_path.exists()
    assert temp_orchestrator.artifacts_dir.exists()


def test_create_new_state(temp_orchestrator):
    """测试创建新状态"""
    state = temp_orchestrator._create_new_state()

    assert state.session_id is not None
    assert state.start_time is not None
    assert state.end_time is None
    assert len(state.steps) == 0
    assert state.overall_state == ExecutionState.RUNNING


def test_save_and_load_state(temp_orchestrator):
    """测试状态保存和加载"""
    # 创建状态
    temp_orchestrator.state = temp_orchestrator._create_new_state()

    # 保存状态
    temp_orchestrator._save_state()
    assert temp_orchestrator.state_file.exists()

    # 加载状态
    loaded_state = temp_orchestrator._load_state()

    assert loaded_state.session_id == temp_orchestrator.state.session_id


def test_save_step_result(temp_orchestrator):
    """测试保存步骤结果"""
    temp_orchestrator.state = temp_orchestrator._create_new_state()

    result = StepResult(
        step_name="sweep",
        state=ExecutionState.SUCCESS,
        start_time="2026-06-23T10:00:00"
    )

    temp_orchestrator._save_step_result("sweep", result)

    assert len(temp_orchestrator.state.steps) == 1
    assert temp_orchestrator.state.steps[0].step_name == "sweep"


def test_should_skip_step(temp_orchestrator):
    """测试步骤跳过逻辑"""
    temp_orchestrator.state = temp_orchestrator._create_new_state()

    # 没有步骤，不应该跳过
    assert not temp_orchestrator._should_skip_step("sweep")

    # 添加成功的步骤
    temp_orchestrator.state.steps.append(
        StepResult(
            step_name="sweep",
            state=ExecutionState.SUCCESS,
            start_time="2026-06-23T10:00:00"
        )
    )

    # 应该跳过
    assert temp_orchestrator._should_skip_step("sweep")

    # 其他步骤不应该跳过
    assert not temp_orchestrator._should_skip_step("reduce")


def test_should_continue_after_failure(temp_orchestrator):
    """测试失败后继续逻辑"""
    # 关键步骤失败，不应该继续
    assert not temp_orchestrator._should_continue_after_failure("sweep")
    assert not temp_orchestrator._should_continue_after_failure("reduce")

    # 非关键步骤失败，应该继续
    assert temp_orchestrator._should_continue_after_failure("patch")
    assert temp_orchestrator._should_continue_after_failure("context_sync")


def test_get_step_result(temp_orchestrator):
    """测试获取步骤结果"""
    temp_orchestrator.state = temp_orchestrator._create_new_state()

    # 不存在的步骤
    assert temp_orchestrator._get_step_result("sweep") is None

    # 添加步骤
    temp_orchestrator.state.steps.append(
        StepResult(
            step_name="sweep",
            state=ExecutionState.SUCCESS,
            start_time="2026-06-23T10:00:00",
            artifacts={"files_scanned": 100}
        )
    )

    # 获取步骤
    result = temp_orchestrator._get_step_result("sweep")
    assert result is not None
    assert result.step_name == "sweep"
    assert result.artifacts["files_scanned"] == 100


def test_finalize_state(temp_orchestrator):
    """测试状态完成"""
    temp_orchestrator.state = temp_orchestrator._create_new_state()

    # 添加步骤
    temp_orchestrator.state.steps.append(
        StepResult(
            step_name="sweep",
            state=ExecutionState.SUCCESS,
            start_time="2026-06-23T10:00:00"
        )
    )
    temp_orchestrator.state.steps.append(
        StepResult(
            step_name="reduce",
            state=ExecutionState.FAILED,
            start_time="2026-06-23T10:05:00",
            error_message="Test error"
        )
    )

    # 完成状态
    temp_orchestrator._finalize_state()

    assert temp_orchestrator.state.end_time is not None
    assert temp_orchestrator.state.overall_state == ExecutionState.PARTIAL_SUCCESS
    assert temp_orchestrator.state.summary["total_steps"] == 2
    assert temp_orchestrator.state.summary["success_steps"] == 1
    assert temp_orchestrator.state.summary["failed_steps"] == 1


@pytest.mark.asyncio
async def test_step_sweep(temp_orchestrator):
    """测试 Sweep 步骤"""
    result = await temp_orchestrator._step_sweep(auto_approve=True)

    assert "files_scanned" in result
    assert isinstance(result["files_scanned"], int)


@pytest.mark.asyncio
async def test_step_reduce(temp_orchestrator):
    """测试 Reduce 步骤"""
    result = await temp_orchestrator._step_reduce(auto_approve=True)

    assert "vulnerabilities_found" in result
    assert isinstance(result["vulnerabilities_found"], int)


@pytest.mark.asyncio
async def test_step_patch(temp_orchestrator):
    """测试 Patch 步骤"""
    result = await temp_orchestrator._step_patch(auto_approve=True)

    assert "vulnerabilities_fixed" in result
    assert isinstance(result["vulnerabilities_fixed"], int)


@pytest.mark.asyncio
async def test_step_context_sync(temp_orchestrator):
    """测试 Context Sync 步骤"""
    result = await temp_orchestrator._step_context_sync(auto_approve=True)

    assert "target_file" in result
    assert "injected" in result


@pytest.mark.asyncio
async def test_run_full_pipeline(tmp_path):
    """测试完整流水线"""
    result = await run_full_pipeline(
        repo_path=tmp_path,
        auto_approve=True,
        continue_from_checkpoint=False
    )

    assert result.session_id is not None
    assert result.overall_state in [
        ExecutionState.SUCCESS,
        ExecutionState.PARTIAL_SUCCESS
    ]
    assert len(result.steps) > 0


@pytest.mark.asyncio
async def test_run_with_checkpoint_recovery(tmp_path):
    """测试检查点恢复"""
    # 第一次运行
    orchestrator1 = AegisOrchestrator(repo_path=tmp_path)
    result1 = await orchestrator1.run(auto_approve=True)

    # 第二次运行（从检查点恢复）
    orchestrator2 = AegisOrchestrator(repo_path=tmp_path)
    result2 = await orchestrator2.run(
        auto_approve=True,
        continue_from_checkpoint=True
    )

    # 验证会话 ID 相同
    assert result1.session_id == result2.session_id


# ==========================================
# 边界情况测试
# ==========================================
def test_load_state_file_not_found(temp_orchestrator):
    """测试加载不存在的状态文件"""
    with pytest.raises(FileNotFoundError):
        temp_orchestrator._load_state()


def test_finalize_state_all_success(temp_orchestrator):
    """测试所有步骤成功"""
    temp_orchestrator.state = temp_orchestrator._create_new_state()

    # 添加所有成功的步骤
    for step_name in ["sweep", "reduce", "patch", "context_sync"]:
        temp_orchestrator.state.steps.append(
            StepResult(
                step_name=step_name,
                state=ExecutionState.SUCCESS,
                start_time="2026-06-23T10:00:00"
            )
        )

    temp_orchestrator._finalize_state()

    assert temp_orchestrator.state.overall_state == ExecutionState.SUCCESS


def test_finalize_state_all_failed(temp_orchestrator):
    """测试所有步骤失败"""
    temp_orchestrator.state = temp_orchestrator._create_new_state()

    # 添加所有失败的步骤
    for step_name in ["sweep", "reduce", "patch", "context_sync"]:
        temp_orchestrator.state.steps.append(
            StepResult(
                step_name=step_name,
                state=ExecutionState.FAILED,
                start_time="2026-06-23T10:00:00",
                error_message="Test error"
            )
        )

    temp_orchestrator._finalize_state()

    assert temp_orchestrator.state.overall_state == ExecutionState.FAILED
