#!/usr/bin/env python3
"""
🛡️ Aegis Box - CLI Entry Point & Config Models
实现 Typer 命令行交互与 Pydantic 严格配置校验。
"""

import os
from pathlib import Path
from enum import Enum
import typer
from typing import Optional, Dict
from pydantic import BaseModel, Field
import yaml
from loguru import logger
from rich.console import Console
from rich.table import Table

app = typer.Typer(
    help="🛡️ Aegis: 全栈智能审计与自愈引擎 (Claude Code / Cursor 的超级外挂)",
    add_completion=False,
)
console = Console()

# ==========================================
# 1. 核心数据模型 (Pydantic)
# ==========================================
class ModelTierConfig(BaseModel):
    """单个模型层级的配置"""
    provider: str = Field(..., description="LLM 提供商 (如 litellm 支持的 openai, anthropic, zhipu, ollama)")
    model: str = Field(..., description="模型名称")
    api_key_env_var: Optional[str] = Field(None, description="读取 API Key 的环境变量名")
    endpoint: Optional[str] = Field(None, description="自定义推理端点 (用于私有化部署)")

class RateLimitConfig(BaseModel):
    """速率限制配置"""
    global_qps: int = Field(default=10, description="全局每秒请求数限制")
    provider_limits: Dict[str, int] = Field(
        default={
            "openai": 50,      # 每分钟请求数
            "anthropic": 40,
            "zhipuai": 100,    # 智谱 AI (LiteLLM 使用 zhipuai)
            "ollama": 1000,    # 本地模型无限制
        },
        description="按提供商的每分钟请求数限制"
    )
    token_bucket_capacity: int = Field(default=1000, description="Token 桶容量")
    token_bucket_refill_rate: int = Field(default=10, description="Token 桶每秒补充速率")

class ASTConfig(BaseModel):
    """AST 提取配置"""
    max_function_lines: int = Field(default=100, description="超过此行数的函数将被截断")
    context_lines: int = Field(default=10, description="截断时保留的头尾行数")
    preserve_comments: list[str] = Field(
        default=["TODO", "FIXME", "HACK", "XXX", "NOTE"],
        description="需要保留的特殊注释标记"
    )
    min_compression_ratio: float = Field(default=0.1, description="AST 压缩的目标比率 (原始行数的10%)")

class GitSandboxConfig(BaseModel):
    """Git 沙盒配置"""
    auto_stash: bool = Field(default=True, description="补丁前自动 stash 未提交更改")
    branch_prefix: str = Field(default="aegis-patch", description="补丁分支前缀")
    verify_syntax: bool = Field(default=True, description="应用补丁后验证语法")

class AegisConfig(BaseModel):
    """Aegis 主配置模型"""
    version: str = Field(default="1.0", description="配置版本号，用于向下兼容和迁移")

    # 核心：三级大模型路由配置
    llm: Dict[str, ModelTierConfig] = Field(
        default={
            "tier1_fast": ModelTierConfig(
                provider="zhipuai",  # LiteLLM 要求使用 zhipuai 而不是 zhipu
                model="glm-4-air",
                api_key_env_var="ZHIPU_API_KEY"
            ),
            "tier2_reasoning": ModelTierConfig(
                provider="anthropic",
                model="claude-3-5-haiku-20241022",
                api_key_env_var="ANTHROPIC_API_KEY"
            ),
            "tier3_patching": ModelTierConfig(
                provider="anthropic",
                model="claude-3-5-sonnet-20241022",
                api_key_env_var="ANTHROPIC_API_KEY"
            ),
        },
        description="三级模型架构: Tier1=快速探伤, Tier2=架构推理, Tier3=补丁生成"
    )

    # 速率限制
    rate_limit: RateLimitConfig = Field(default_factory=RateLimitConfig)

    # AST 提取
    ast: ASTConfig = Field(default_factory=ASTConfig)

    # Git 沙盒
    git: GitSandboxConfig = Field(default_factory=GitSandboxConfig)

    # 全栈忽略名单
    ignore_dirs: list[str] = Field(
        default=[".git", ".idea", ".vscode", "node_modules", "venv", "__pycache__", "dist", "build", ".next", ".nuxt"]
    )

    ignore_extensions: list[str] = Field(
        default=[".pyc", ".pyo", ".so", ".dll", ".dylib", ".class", ".o", ".a", ".log", ".lock"]
    )

    # 补丁容错率
    fuzzy_match_threshold: float = Field(default=0.85, description="SEARCH块的模糊匹配阈值 (0-1)")

# ==========================================
# 2. 配置管理器
# ==========================================
class ConfigManager:
    """配置加载与版本迁移管理器（集成 ConfigLoader）"""

    CONFIG_FILE = "aegis.yaml"
    SUPPORTED_VERSIONS = ["1.0"]

    @classmethod
    def load(cls, project_root: Path = Path.cwd()) -> AegisConfig:
        """
        加载并校验项目根目录的 aegis.yaml

        新增：支持 .env + aegis.yaml 统一加载
        优先级：环境变量 > aegis.yaml > 默认值
        """
        from aegis.core.config import ConfigLoader

        config_path = project_root / cls.CONFIG_FILE

        if not config_path.exists():
            logger.info("未找到配置文件，使用默认配置")
            return AegisConfig()

        try:
            # 使用统一配置加载器
            loader = ConfigLoader(project_root)
            data = loader.load()

            # 版本检查与迁移逻辑
            config_version = data.get("version", "0.0")
            if config_version not in cls.SUPPORTED_VERSIONS:
                logger.warning(
                    f"⚠️ 检测到不兼容的配置版本 (v{config_version})，"
                    f"当前支持: {cls.SUPPORTED_VERSIONS}。"
                    f"建议运行 `aegis config migrate`"
                )

            config = AegisConfig(**data)
            logger.success(f"✅ 配置加载成功 (v{config.version})")
            return config

        except Exception as e:
            logger.error(f"配置加载失败: {e}")
            logger.info("使用默认配置")
            return AegisConfig()

    @classmethod
    def save(cls, config: AegisConfig, project_root: Path = Path.cwd(), use_env_refs: bool = True):
        """
        保存配置到文件

        Args:
            config: 配置对象
            project_root: 项目根目录
            use_env_refs: 是否在模型配置中使用环境变量引用（推荐）
        """
        config_path = project_root / cls.CONFIG_FILE
        config_dict = config.model_dump(mode="json")

        # 如果启用环境变量引用，转换模型配置
        if use_env_refs and "llm" in config_dict:
            for tier_name, tier_config in config_dict["llm"].items():
                if "model" in tier_config:
                    # 生成环境变量引用格式
                    provider = tier_config.get("provider", "").upper()
                    tier_upper = tier_name.replace("_", "").upper()

                    # 使用 provider_MODEL_TIER 格式
                    if provider:
                        env_var = f"{provider}_MODEL_{tier_upper.replace('TIER', 'TIER')}"
                    else:
                        env_var = f"MODEL_{tier_upper}"

                    # 使用默认值作为 fallback
                    default_model = tier_config["model"]
                    tier_config["model"] = f"${{{env_var}:-{default_model}}}"

        with open(config_path, "w", encoding="utf-8") as f:
            # 添加友好的注释头
            f.write("# 🛡️ Aegis Box Configuration\n")
            f.write("#\n")
            f.write("# Model configuration supports environment variable references:\n")
            f.write("#   ${VAR_NAME:-default_value}\n")
            f.write("#\n")
            f.write("# Set your API keys and model overrides in .env file\n")
            f.write("# See .env.example for all available options\n")
            f.write("#\n\n")

            yaml.dump(
                config_dict,
                f,
                default_flow_style=False,
                allow_unicode=True,
                sort_keys=False
            )

# ==========================================
# 3. CLI 命令
# ==========================================

@app.command()
def init(
    force: bool = typer.Option(False, "--force", "-f", help="强制覆盖已存在的配置文件")
):
    """初始化项目，生成默认的 aegis.yaml 配置文件和 .env 提示"""
    config_path = Path.cwd() / ConfigManager.CONFIG_FILE
    env_path = Path.cwd() / ".env"

    if config_path.exists() and not force:
        console.print(f"[yellow]⚠️ 配置文件 {config_path} 已存在。使用 --force 强制覆盖。[/yellow]")
        return

    # 生成 aegis.yaml（使用环境变量引用）
    default_config = AegisConfig()
    ConfigManager.save(default_config, use_env_refs=True)

    console.print(f"[green]✅ 成功生成 {ConfigManager.CONFIG_FILE}！[/green]")

    # 检查 .env 文件
    if not env_path.exists():
        console.print("\n[yellow]⚠️  未找到 .env 文件[/yellow]")
        console.print("[cyan]请创建 .env 文件并设置你的 API Keys：[/cyan]")
        console.print("\n  [dim]# 快速创建（如果项目根目录有 .env.example）[/dim]")
        console.print("  cp .env.example .env")
        console.print("\n  [dim]# 或手动创建并添加以下内容：[/dim]")
        console.print("  [green]ANTHROPIC_API_KEY[/green]=your-key-here")
        console.print("  [green]ZHIPU_API_KEY[/green]=your-key-here")
        console.print("\n  [dim]# 可选：覆盖模型配置[/dim]")
        console.print("  [green]ZHIPU_MODEL_TIER1[/green]=glm-4-air")
        console.print("  [green]ANTHROPIC_MODEL_TIER2[/green]=claude-3-5-haiku-20241022")
        console.print("  [green]ANTHROPIC_MODEL_TIER3[/green]=claude-3-5-sonnet-20241022")
    else:
        console.print(f"\n[green]✅ 已存在 .env 文件: {env_path}[/green]")

    console.print("\n[cyan]💡 提示：模型配置支持环境变量引用，优先级：[/cyan]")
    console.print("   [dim]环境变量 > aegis.yaml > 默认值[/dim]")

@app.command()
def config(
    action: str = typer.Argument("show", help="操作: show=显示配置, migrate=版本迁移")
):
    """配置管理命令"""
    if action == "show":
        config = ConfigManager.load()

        # 使用 Rich 表格展示配置
        table = Table(title="🛡️ Aegis 配置概览", show_header=True)
        table.add_column("配置项", style="cyan")
        table.add_column("值", style="green")

        table.add_row("版本", config.version)
        table.add_row("Tier1 模型", f"{config.llm['tier1_fast'].provider}/{config.llm['tier1_fast'].model}")
        table.add_row("Tier2 模型", f"{config.llm['tier2_reasoning'].provider}/{config.llm['tier2_reasoning'].model}")
        table.add_row("Tier3 模型", f"{config.llm['tier3_patching'].provider}/{config.llm['tier3_patching'].model}")
        table.add_row("全局 QPS", str(config.rate_limit.global_qps))
        table.add_row("模糊匹配阈值", f"{config.fuzzy_match_threshold:.0%}")
        table.add_row("忽略目录", ", ".join(config.ignore_dirs[:5]) + "...")

        console.print(table)

    elif action == "migrate":
        console.print("[yellow]🚧 配置迁移功能将在后续版本实现...[/yellow]")

    else:
        console.print(f"[red]未知操作: {action}[/red]")

@app.command()
def sweep(
    dry_run: bool = typer.Option(True, "--dry-run/--execute", help="仅预览，不实际删除文件"),
    path: str = typer.Option(".", "--path", "-p", help="要清理的目录路径")
):
    """🧹 资产清道夫：物理扫描并清理规则垃圾"""
    config = ConfigManager.load()
    console.print(f"[bold blue]🚀 启动 Asset Sweeper (Dry Run: {dry_run})[/bold blue]")
    console.print(f"目标路径: {path}")
    console.print(f"忽略目录规则: {', '.join(config.ignore_dirs[:5])}...")
    console.print(f"忽略扩展名: {', '.join(config.ignore_extensions[:5])}...")

    # TODO: Phase 2 - 接入多线程物理扫描逻辑
    console.print("[yellow]🚧 清理引擎核心逻辑将在 Phase 2 实装...[/yellow]")

@app.command()
def audit(
    module: str = typer.Argument(".", help="指定要审计的目录"),
    output: Optional[str] = typer.Option(None, "--output", "-o", help="输出报告路径"),
    ci_mode: bool = typer.Option(False, "--ci-mode", help="CI/CD 模式：静默运行，生成 Markdown 报告")
):
    """🧠 架构审计：提取 AST 并调用 Tier1 & Tier2 模型进行降维分析"""
    config = ConfigManager.load()

    if ci_mode:
        # CI/CD 模式
        console.print("[bold blue]🤖 CI/CD 模式：开始自动审计...[/bold blue]")

        try:
            from aegis.engines.context_injector import run_ci_audit

            result = run_ci_audit(project_root=Path(module))

            if result["success"]:
                console.print("[green]✅ CI 审计完成[/green]")
                console.print(result["markdown_report"])

                # 保存报告
                if output:
                    Path(output).write_text(result["markdown_report"], encoding="utf-8")
                    console.print(f"[cyan]📄 报告已保存到 {output}[/cyan]")
            else:
                console.print(f"[red]❌ CI 审计失败: {result.get('error')}[/red]")
                raise typer.Exit(code=1)

        except Exception as e:
            console.print(f"[red]❌ CI 审计异常: {e}[/red]")
            raise typer.Exit(code=1)
    else:
        # 普通模式
        console.print(f"[bold magenta]🔍 启动架构探针... 目标: {module}[/bold magenta]")

        # 显示模型配置
        table = Table(title="模型路由配置", show_header=True)
        table.add_column("层级", style="cyan")
        table.add_column("模型", style="green")
        table.add_column("用途", style="yellow")

        table.add_row("Tier 1", config.llm['tier1_fast'].model, "切片探伤 (快速)")
        table.add_row("Tier 2", config.llm['tier2_reasoning'].model, "架构总结 (推理)")

        console.print(table)

        # TODO: Phase 2 - 接入 tree-sitter AST 提取与双轨归纳逻辑
        console.print("[yellow]🚧 AST 提取器与架构归纳将在 Phase 2 实装...[/yellow]")

@app.command()
def patch(
    files: Optional[list[str]] = typer.Argument(None, help="要打补丁的文件列表"),
    review: bool = typer.Option(False, "--review", help="应用前展示 diff 供人工审查")
):
    """🩹 智能自愈：调用 Tier3 生成补丁并执行企业级 Git 沙盒柔性合并"""
    config = ConfigManager.load()
    console.print("[bold red]🚨 启动自愈引擎与 Git 安全沙盒[/bold red]")
    console.print(f"Tier3 旗舰补丁模型: {config.llm['tier3_patching'].model}")
    console.print(f"模糊匹配容错率: {config.fuzzy_match_threshold * 100:.0f}%")
    console.print(f"Git 沙盒配置: auto_stash={config.git.auto_stash}, verify_syntax={config.git.verify_syntax}")

    # TODO: Phase 3 - 接入 Fuzzy SequenceMatcher 与 GitPython 逻辑
    console.print("[yellow]🚧 补丁生成与安全沙盒将在 Phase 3 实装...[/yellow]")

@app.command(name="context-sync")
def context_sync(
    remove: bool = typer.Option(False, "--remove", help="移除 Aegis 上下文"),
    format: str = typer.Option("cursorrules", "--format", "-f", help="目标格式: cursorrules 或 claude_xml")
):
    """🔄 上下文同步：将审计结果同步到 IDE 配置文件（.cursorrules / .claude_context.xml）"""
    console.print("[bold cyan]🔄 开始上下文同步...[/bold cyan]")

    try:
        from aegis.engines.context_injector import ContextInjector
        from aegis.engines.patcher import Vulnerability, ArchitectureReport

        injector = ContextInjector(
            project_root=Path.cwd(),
            target_format=format
        )

        if remove:
            # 移除模式
            result = injector.remove_context()

            if result.success:
                console.print(f"[green]✅ 已移除 Aegis 上下文: {result.target_file}[/green]")
            else:
                console.print(f"[red]❌ 移除失败: {result.error_message}[/red]")
                raise typer.Exit(code=1)
        else:
            # 注入模式
            console.print(f"[cyan]目标格式: {format}[/cyan]")

            # TODO: 实际场景应该从审计报告中读取
            # 这里使用示例数据
            sample_report = ArchitectureReport(
                critical_vulnerabilities=[
                    Vulnerability(
                        file_path="user_service.py",
                        description="SQL injection in get_user function",
                        severity="CRITICAL",
                        suggestion="Use parameterized queries"
                    )
                ]
            )

            result = injector.inject_context(sample_report)

            if result.success:
                console.print(f"[green]✅ 上下文已注入: {result.target_file}[/green]")
                console.print("[cyan]💡 IDE 将自动遵守这些架构约束和安全规范[/cyan]")
            else:
                console.print(f"[red]❌ 注入失败: {result.error_message}[/red]")
                raise typer.Exit(code=1)

    except ImportError as e:
        console.print(f"[red]❌ 导入失败: {e}[/red]")
        console.print("[yellow]请确保已正确安装 Aegis 依赖[/yellow]")
        raise typer.Exit(code=1)
    except Exception as e:
        console.print(f"[red]❌ 上下文同步失败: {e}[/red]")
        raise typer.Exit(code=1)

@app.command()
def run(
    auto: bool = typer.Option(False, "--auto", help="全自动模式：无需确认，静默执行"),
    yes: bool = typer.Option(False, "--yes", "-y", help="自动批准所有步骤"),
    continue_flag: bool = typer.Option(False, "--continue", help="从上次检查点恢复执行")
):
    """🚀 运行完整的 Aegis 流水线：Sweep -> Audit -> Patch -> Context Sync"""
    import asyncio

    if auto:
        yes = True  # --auto 隐含 --yes

    console.print("[bold blue]🚀 启动 Aegis 全链路编排...[/bold blue]")

    if continue_flag:
        console.print("[cyan]📂 从检查点恢复执行...[/cyan]")

    if yes:
        console.print("[yellow]⚡ 自动批准模式：将跳过所有确认步骤[/yellow]")

    try:
        from aegis.engines.orchestrator import run_full_pipeline

        # 运行异步流水线
        result = asyncio.run(run_full_pipeline(
            repo_path=Path.cwd(),
            auto_approve=yes,
            continue_from_checkpoint=continue_flag
        ))

        # 显示结果
        if result.overall_state.value == "success":
            console.print("\n[bold green]✅ 全链路执行成功！[/bold green]")
        elif result.overall_state.value == "partial_success":
            console.print("\n[bold yellow]⚠️  部分成功：部分步骤失败[/bold yellow]")
            console.print("[cyan]请查看 artifacts/aegis_state.json 了解详情[/cyan]")
        else:
            console.print("\n[bold red]❌ 执行失败[/bold red]")
            raise typer.Exit(code=1)

    except ImportError as e:
        console.print(f"[red]❌ 导入失败: {e}[/red]")
        console.print("[yellow]请确保已正确安装 Aegis 依赖[/yellow]")
        raise typer.Exit(code=1)
    except FileNotFoundError as e:
        if continue_flag:
            console.print(f"[red]❌ 未找到检查点文件: {e}[/red]")
            console.print("[yellow]请先运行 'aegis run' 创建初始状态[/yellow]")
        else:
            console.print(f"[red]❌ 文件错误: {e}[/red]")
        raise typer.Exit(code=1)
    except Exception as e:
        console.print(f"[red]❌ 执行失败: {e}[/red]")
        raise typer.Exit(code=1)

@app.command()
def version():
    """显示版本信息"""
    from aegis import __version__
    console.print(f"[bold green]🛡️ Aegis Box v{__version__}[/bold green]")
    console.print("全栈智能审计与自愈引擎")

if __name__ == "__main__":
    app()
