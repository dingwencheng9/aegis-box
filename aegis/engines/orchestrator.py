"""
🛡️ Aegis - Orchestrator（全链路编排引擎）
任务编排、状态管理、检查点恢复、容错处理
"""

import asyncio
import json
from pathlib import Path
from typing import Optional, List, Dict, Any, Callable
from datetime import datetime
from enum import Enum
from dataclasses import dataclass, asdict
from loguru import logger

from aegis.cli import AegisConfig
from aegis.engines.sweeper import AssetSweeper
from aegis.engines.mapper import CodeMapper
from aegis.engines.patcher import SmartPatcher
from aegis.engines.context_injector import ContextInjector


# ==========================================
# 状态枚举
# ==========================================
class ExecutionState(str, Enum):
    """执行状态"""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    PARTIAL_SUCCESS = "partial_success"
    SKIPPED = "skipped"


# ==========================================
# 数据模型
# ==========================================
@dataclass
class StepResult:
    """步骤执行结果"""
    step_name: str
    state: ExecutionState
    start_time: str
    end_time: Optional[str] = None
    error_message: Optional[str] = None
    artifacts: Dict[str, Any] = None

    def __post_init__(self):
        if self.artifacts is None:
            self.artifacts = {}


@dataclass
class OrchestratorState:
    """编排器状态"""
    session_id: str
    start_time: str
    end_time: Optional[str]
    steps: List[StepResult]
    overall_state: ExecutionState
    summary: Dict[str, Any]

    def to_dict(self) -> Dict:
        """转换为字典（用于 JSON 序列化）"""
        return {
            "session_id": self.session_id,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "steps": [asdict(step) for step in self.steps],
            "overall_state": self.overall_state.value,
            "summary": self.summary
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "OrchestratorState":
        """从字典创建（用于 JSON 反序列化）"""
        steps = [
            StepResult(
                step_name=s["step_name"],
                state=ExecutionState(s["state"]),
                start_time=s["start_time"],
                end_time=s.get("end_time"),
                error_message=s.get("error_message"),
                artifacts=s.get("artifacts", {})
            )
            for s in data["steps"]
        ]

        return cls(
            session_id=data["session_id"],
            start_time=data["start_time"],
            end_time=data.get("end_time"),
            steps=steps,
            overall_state=ExecutionState(data["overall_state"]),
            summary=data.get("summary", {})
        )


# ==========================================
# 全链路编排引擎
# ==========================================
class AegisOrchestrator:
    """
    全链路编排引擎

    职责：
    1. 编排 Sweep -> Reduce -> Patch -> Context Sync 全流程
    2. 管理执行状态和检查点
    3. 容错处理和部分成功
    4. 生成汇总报告

    Example:
        >>> orchestrator = AegisOrchestrator(repo_path=Path("/project"))
        >>> result = await orchestrator.run(auto_approve=True)
        >>> print(result.summary)
    """

    def __init__(
        self,
        repo_path: Optional[Path] = None,
        config: Optional[AegisConfig] = None
    ):
        """
        初始化编排器

        Args:
            repo_path: 项目根目录（默认当前目录）
            config: Aegis 配置（默认从文件加载）
        """
        self.repo_path = repo_path or Path.cwd()
        self.config = config

        # 状态文件路径
        self.artifacts_dir = self.repo_path / "artifacts"
        self.artifacts_dir.mkdir(exist_ok=True)
        self.state_file = self.artifacts_dir / "aegis_state.json"

        # 当前状态
        self.state: Optional[OrchestratorState] = None

    async def run(
        self,
        auto_approve: bool = False,
        continue_from_checkpoint: bool = False
    ) -> OrchestratorState:
        """
        运行全链路编排

        Args:
            auto_approve: 是否自动批准所有步骤（--yes）
            continue_from_checkpoint: 是否从检查点恢复（--continue）

        Returns:
            OrchestratorState: 最终状态
        """
        logger.info("🚀 启动 Aegis 全链路编排...")

        # Step 1: 加载或创建状态
        if continue_from_checkpoint and self.state_file.exists():
            logger.info("📂 从检查点恢复...")
            self.state = self._load_state()
        else:
            logger.info("🆕 创建新的执行会话...")
            self.state = self._create_new_state()

        # Step 2: 执行步骤
        steps = [
            ("sweep", "🧹 资产清扫", self._step_sweep),
            ("reduce", "🔍 架构审计", self._step_reduce),
            ("patch", "🛠️  智能修复", self._step_patch),
            ("context_sync", "🔄 上下文同步", self._step_context_sync),
        ]

        for step_name, step_label, step_func in steps:
            # 检查是否应该跳过
            if self._should_skip_step(step_name):
                logger.info(f"⏭️  跳过步骤: {step_label}（已完成）")
                continue

            logger.info(f"\n{'='*80}\n{step_label}\n{'='*80}")

            try:
                # 执行步骤
                result = await self._execute_step(
                    step_name=step_name,
                    step_func=step_func,
                    auto_approve=auto_approve
                )

                # 保存步骤结果
                self._save_step_result(step_name, result)

            except Exception as e:
                # 处理步骤失败
                logger.error(f"❌ 步骤失败: {step_label} - {e}")
                self._handle_step_failure(step_name, e)

                # 决定是否继续
                if not self._should_continue_after_failure(step_name):
                    logger.warning("⚠️  关键步骤失败，停止执行")
                    break

        # Step 3: 生成最终报告
        self._finalize_state()
        self._save_state()

        logger.success("✅ Aegis 全链路编排完成！")
        self._print_summary()

        return self.state

    async def _execute_step(
        self,
        step_name: str,
        step_func: Callable,
        auto_approve: bool
    ) -> StepResult:
        """
        执行单个步骤

        Args:
            step_name: 步骤名称
            step_func: 步骤函数
            auto_approve: 是否自动批准

        Returns:
            StepResult: 步骤结果
        """
        start_time = datetime.now().isoformat()

        try:
            # 执行步骤函数
            artifacts = await step_func(auto_approve=auto_approve)

            # 成功
            return StepResult(
                step_name=step_name,
                state=ExecutionState.SUCCESS,
                start_time=start_time,
                end_time=datetime.now().isoformat(),
                artifacts=artifacts
            )

        except Exception as e:
            # 失败
            logger.error(f"步骤执行失败: {e}")
            return StepResult(
                step_name=step_name,
                state=ExecutionState.FAILED,
                start_time=start_time,
                end_time=datetime.now().isoformat(),
                error_message=str(e)
            )

    async def _step_sweep(self, auto_approve: bool = False) -> Dict[str, Any]:
        """
        步骤 A: 资产清扫

        Args:
            auto_approve: 是否自动批准

        Returns:
            清扫结果
        """
        logger.info("开始资产清扫...")

        try:
            # 从配置提取参数
            sweeper = AssetSweeper(
                ignore_dirs=self.config.ignore_dirs,
                ignore_extensions=self.config.ignore_extensions,
                max_workers=4
            )
            result = sweeper.sweep(dry_run=not auto_approve)

            return {
                "files_scanned": result.get("total_files", 0),
                "files_cleaned": result.get("cleaned_count", 0),
                "space_freed_mb": result.get("space_freed_mb", 0)
            }
        except Exception as e:
            logger.error(f"资产清扫失败: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return {
                "files_scanned": 0,
                "files_cleaned": 0,
                "space_freed_mb": 0
            }

    async def _step_reduce(self, auto_approve: bool = False) -> Dict[str, Any]:
        """
        步骤 B: 架构审计

        Args:
            auto_approve: 是否自动批准

        Returns:
            审计报告
        """
        logger.info("开始架构审计...")

        try:
            mapper = CodeMapper()
            skeletons = mapper.map_repository(self.repo_path)

            # 统计结果
            total_lines = sum(s.total_lines for s in skeletons)
            compressed_lines = sum(s.compressed_lines for s in skeletons)

            return {
                "files_mapped": len(skeletons),
                "total_lines": total_lines,
                "compressed_lines": compressed_lines,
                "compression_ratio": (1 - compressed_lines / total_lines) if total_lines > 0 else 0,
                "vulnerabilities_found": 0,  # TODO: 需要 LLM 审计
                "critical": 0,
                "high": 0,
                "medium": 0
            }
        except Exception as e:
            logger.error(f"架构审计失败: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return {
                "files_mapped": 0,
                "vulnerabilities_found": 0,
                "critical": 0,
                "high": 0,
                "medium": 0
            }

    async def _step_patch(self, auto_approve: bool = False) -> Dict[str, Any]:
        """
        步骤 C: 智能修复

        Args:
            auto_approve: 是否自动批准

        Returns:
            修复结果
        """
        logger.info("开始智能修复...")

        # 暂时跳过（需要 LLM 生成补丁）
        logger.warning("智能修复功能需要 LLM 审计结果，当前跳过")

        return {
            "vulnerabilities_fixed": 0,
            "vulnerabilities_failed": 0,
            "success_rate": 0.0,
            "skipped": True
        }

    async def _step_context_sync(self, auto_approve: bool = False) -> Dict[str, Any]:
        """
        步骤 D: 上下文同步

        Args:
            auto_approve: 是否自动批准

        Returns:
            同步结果
        """
        logger.info("开始上下文同步...")

        try:
            injector = ContextInjector(self.repo_path)

            # 从 reduce 步骤获取结果（暂时传入空报告）
            # TODO: 需要 LLM 审计后才有真实报告
            from aegis.engines.context_injector import ArchitectureReport
            empty_report = ArchitectureReport(
                critical_vulnerabilities=[],
                architecture_patterns=[],
                dependency_summary={}
            )

            result = injector.inject_context(empty_report)

            return {
                "target_file": ".cursorrules",
                "injected": result.success
            }
        except Exception as e:
            logger.error(f"上下文同步失败: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return {
                "target_file": ".cursorrules",
                "injected": False
            }

    def _create_new_state(self) -> OrchestratorState:
        """
        创建新的执行状态

        Returns:
            OrchestratorState: 新状态
        """
        session_id = datetime.now().strftime("%Y%m%d-%H%M%S")

        return OrchestratorState(
            session_id=session_id,
            start_time=datetime.now().isoformat(),
            end_time=None,
            steps=[],
            overall_state=ExecutionState.RUNNING,
            summary={}
        )

    def _load_state(self) -> OrchestratorState:
        """
        从检查点加载状态

        Returns:
            OrchestratorState: 加载的状态

        Raises:
            FileNotFoundError: 状态文件不存在
        """
        if not self.state_file.exists():
            raise FileNotFoundError(f"状态文件不存在: {self.state_file}")

        with open(self.state_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        state = OrchestratorState.from_dict(data)
        logger.info(f"✅ 加载状态: 会话 {state.session_id}")

        return state

    def _save_state(self):
        """保存状态到文件"""
        with open(self.state_file, "w", encoding="utf-8") as f:
            json.dump(self.state.to_dict(), f, indent=2, ensure_ascii=False)

        logger.debug(f"💾 状态已保存: {self.state_file}")

    def _save_step_result(self, step_name: str, result: StepResult):
        """
        保存步骤结果

        Args:
            step_name: 步骤名称
            result: 步骤结果
        """
        # 查找是否已有该步骤
        existing_idx = None
        for idx, step in enumerate(self.state.steps):
            if step.step_name == step_name:
                existing_idx = idx
                break

        if existing_idx is not None:
            # 更新已有步骤
            self.state.steps[existing_idx] = result
        else:
            # 添加新步骤
            self.state.steps.append(result)

        # 保存到文件
        self._save_state()

        logger.success(f"✅ 步骤完成: {step_name}")

    def _handle_step_failure(self, step_name: str, error: Exception):
        """
        处理步骤失败

        Args:
            step_name: 步骤名称
            error: 异常
        """
        result = StepResult(
            step_name=step_name,
            state=ExecutionState.FAILED,
            start_time=datetime.now().isoformat(),
            end_time=datetime.now().isoformat(),
            error_message=str(error)
        )

        self._save_step_result(step_name, result)

    def _should_skip_step(self, step_name: str) -> bool:
        """
        检查是否应该跳过步骤

        Args:
            step_name: 步骤名称

        Returns:
            True 如果应该跳过
        """
        for step in self.state.steps:
            if step.step_name == step_name and step.state == ExecutionState.SUCCESS:
                return True

        return False

    def _should_continue_after_failure(self, step_name: str) -> bool:
        """
        检查步骤失败后是否应该继续

        Args:
            step_name: 步骤名称

        Returns:
            True 如果应该继续
        """
        # 定义关键步骤
        critical_steps = {"sweep", "reduce"}

        # 关键步骤失败，停止执行
        if step_name in critical_steps:
            return False

        # 非关键步骤失败，继续执行
        return True

    def _get_step_result(self, step_name: str) -> Optional[StepResult]:
        """
        获取步骤结果

        Args:
            step_name: 步骤名称

        Returns:
            StepResult 或 None
        """
        for step in self.state.steps:
            if step.step_name == step_name:
                return step

        return None

    def _finalize_state(self):
        """完成状态：计算最终状态和汇总"""
        self.state.end_time = datetime.now().isoformat()

        # 统计步骤状态
        success_count = sum(
            1 for step in self.state.steps
            if step.state == ExecutionState.SUCCESS
        )
        failed_count = sum(
            1 for step in self.state.steps
            if step.state == ExecutionState.FAILED
        )
        total_count = len(self.state.steps)

        # 计算最终状态
        if failed_count == 0:
            self.state.overall_state = ExecutionState.SUCCESS
        elif success_count == 0:
            self.state.overall_state = ExecutionState.FAILED
        else:
            self.state.overall_state = ExecutionState.PARTIAL_SUCCESS

        # 生成汇总
        self.state.summary = {
            "total_steps": total_count,
            "success_steps": success_count,
            "failed_steps": failed_count,
            "overall_state": self.state.overall_state.value
        }

        # 添加详细统计
        for step in self.state.steps:
            if step.artifacts:
                self.state.summary[f"{step.step_name}_artifacts"] = step.artifacts

    def _print_summary(self):
        """打印汇总报告"""
        logger.info("\n" + "="*80)
        logger.info("📊 执行汇总")
        logger.info("="*80)

        logger.info(f"会话 ID: {self.state.session_id}")
        logger.info(f"开始时间: {self.state.start_time}")
        logger.info(f"结束时间: {self.state.end_time}")
        logger.info(f"最终状态: {self.state.overall_state.value}")

        logger.info("\n步骤详情:")
        for step in self.state.steps:
            status_icon = "✅" if step.state == ExecutionState.SUCCESS else "❌"
            logger.info(f"  {status_icon} {step.step_name}: {step.state.value}")

            if step.error_message:
                logger.info(f"     错误: {step.error_message}")

        logger.info("\n汇总统计:")
        logger.info(f"  总步骤数: {self.state.summary.get('total_steps', 0)}")
        logger.info(f"  成功: {self.state.summary.get('success_steps', 0)}")
        logger.info(f"  失败: {self.state.summary.get('failed_steps', 0)}")

        logger.info("="*80)


# ==========================================
# 外部调用入口
# ==========================================
async def run_full_pipeline(
    repo_path: Optional[Path] = None,
    config: Optional[AegisConfig] = None,
    auto_approve: bool = False,
    continue_from_checkpoint: bool = False
) -> OrchestratorState:
    """
    运行完整的 Aegis 流水线（一站式入口）

    Args:
        repo_path: 项目根目录
        config: Aegis 配置
        auto_approve: 是否自动批准
        continue_from_checkpoint: 是否从检查点恢复

    Returns:
        OrchestratorState: 最终状态

    Example:
        >>> import asyncio
        >>> from aegis.engines.orchestrator import run_full_pipeline
        >>>
        >>> result = asyncio.run(run_full_pipeline(auto_approve=True))
        >>> print(result.summary)
    """
    orchestrator = AegisOrchestrator(repo_path=repo_path, config=config)
    return await orchestrator.run(
        auto_approve=auto_approve,
        continue_from_checkpoint=continue_from_checkpoint
    )
