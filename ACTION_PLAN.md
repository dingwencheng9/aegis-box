# 🎯 Aegis Box 改进行动计划

基于深度自身审查报告，这是一份可执行的改进路线图。

---

## 📊 优先级说明

- **🔴 P0 (Critical)**: 阻碍核心功能，1周内必须修复
- **🟡 P1 (High)**: 影响质量和可维护性，2-4周内完成
- **🟢 P2 (Medium)**: 增强功能，1-3个月内完成

---

## 🔴 P0 - 立即修复（1周内）

### 1. 修复测试环境 [1天]

**问题**: 测试无法运行，依赖未安装

```bash
# 步骤
cd /Users/nexo/projects/aegis_box
uv sync --all-extras
pytest tests/ -v
pytest tests/ --cov=aegis --cov-report=html --cov-report=term-missing
```

**验收标准**:

- [ ] 所有测试可以运行
- [ ] 测试覆盖率 ≥ 60% (目标 80%)

---

### 2. 实现 LLM 审计核心功能 [3天]

**问题**: `orchestrator.py:387` 漏洞检测是占位符

**当前代码**:

```python
"vulnerabilities_found": 0,  # TODO: 需要 LLM 审计
```

**需要实现**:

```python
# orchestrator.py:_step_reduce()
async def _step_reduce(self, config: AegisConfig):
    # 1. 生成 AST 骨架
    mapper = CodeMapper(...)
    skeletons = mapper.map_repository(self.repo_path)

    # 2. 调用 LLM 审计
    from aegis.engines.reducer import ArchitectureReducer
    reducer = ArchitectureReducer(llm_client=self.tier2_client)
    report = await reducer.analyze(skeletons)

    # 3. 返回真实漏洞数
    return {
        "vulnerabilities_found": len(report.vulnerabilities),
        "critical": len([v for v in report.vulnerabilities if v.severity == "critical"]),
        ...
    }
```

**验收标准**:

- [ ] 能检测到真实漏洞（在测试代码中验证）
- [ ] 能在自身代码上运行（Ouroboros 测试）

---

### 3. 修复安全漏洞 [2天]

#### 3.1 输入验证 - mapper.py

**文件**: `aegis/engines/mapper.py:80`

```python
# 修复前
def to_markdown(self, max_function_lines: int = 100, context_lines: int = 10):
    # 无验证

# 修复后
def to_markdown(self, max_function_lines: int = 100, context_lines: int = 10):
    if not (1 <= max_function_lines <= 10000):
        raise ValueError("max_function_lines must be between 1 and 10000")
    if not (0 <= context_lines <= 100):
        raise ValueError("context_lines must be between 0 and 100")
    # ...
```

#### 3.2 路径遍历防护 - sweeper.py

**文件**: `aegis/engines/sweeper.py`

```python
# 修复
def scan_directory(self, root_path: Path) -> List[Path]:
    root_path = root_path.resolve()  # 解析符号链接
    cwd = Path.cwd().resolve()
    if not root_path.is_relative_to(cwd):
        raise ValueError(f"Path traversal detected: {root_path} is outside {cwd}")
    # ...
```

#### 3.3 日志脱敏

**新增文件**: `aegis/utils/log_sanitizer.py`

```python
from typing import Any, Dict

def sanitize_log_data(data: Any) -> Any:
    """脱敏日志中的敏感信息"""
    if isinstance(data, dict):
        sensitive_keys = {
            "api_key", "token", "password", "secret",
            "authorization", "api-key", "x-api-key"
        }
        return {
            k: "***REDACTED***" if k.lower() in sensitive_keys else sanitize_log_data(v)
            for k, v in data.items()
        }
    elif isinstance(data, (list, tuple)):
        return type(data)(sanitize_log_data(item) for item in data)
    return data
```

**验收标准**:

- [ ] 通过安全扫描（bandit）
- [ ] 添加对应的单元测试

---

## 🟡 P1 - 重要改进（2-4周）

### 4. 清理代码质量问题 [1周]

**问题**: 907个 Ruff 问题

```bash
# 步骤 1: 自动修复
ruff check aegis/ --fix

# 步骤 2: 手动审查并修复剩余问题
ruff check aegis/ --statistics

# 步骤 3: 添加 pre-commit hook
pip install pre-commit
pre-commit install
```

**重点关注**:

- [ ] B904: 修复 7 处异常链断裂
- [ ] UP035: 更新 23 处废弃导入
- [ ] F401: 移除 17 处未使用导入

**验收标准**:

- [ ] Ruff 错误 < 50 个
- [ ] 无 HIGH 严重性问题

---

### 5. 完善文档 [1周]

#### 5.1 生成 API 文档

```bash
pip install mkdocs mkdocs-material mkdocstrings[python]
mkdocs new .
```

**创建**: `docs/api/`

- `core.md` - 核心模块文档
- `engines.md` - 引擎模块文档
- `utils.md` - 工具模块文档

#### 5.2 配置文档

**创建**: `docs/CONFIGURATION.md`

```markdown
# Aegis Box 配置指南

## 基础配置

### LLM 提供商配置

...

### 速率限制配置

...

### AST 提取配置

...
```

**验收标准**:

- [ ] API 文档可通过 `mkdocs serve` 访问
- [ ] 所有公共 API 有文档字符串

---

### 6. 引入架构改进 [2周]

#### 6.1 Engine 抽象层

**新增文件**: `aegis/engines/base.py`

```python
from abc import ABC, abstractmethod
from typing import Dict, Any
from dataclasses import dataclass

@dataclass
class ExecutionContext:
    """引擎执行上下文"""
    repo_path: Path
    config: AegisConfig
    state: Dict[str, Any]

class Engine(ABC):
    """引擎抽象基类"""

    @abstractmethod
    async def execute(self, context: ExecutionContext) -> StepResult:
        """执行引擎逻辑"""
        pass

    @abstractmethod
    def validate(self, context: ExecutionContext) -> bool:
        """验证是否可以执行"""
        pass
```

**修改**: `aegis/engines/sweeper.py`, `mapper.py`, 等

```python
class AssetSweeper(Engine):
    async def execute(self, context: ExecutionContext) -> StepResult:
        # 实现
```

#### 6.2 优化 LLM 客户端工厂

**修改**: `aegis/engines/patcher.py`

```python
class SmartPatcher:
    def __init__(self, ...):
        self.llm_factory = LLMClientFactory()
        self._tier3_client: Optional[LLMClient] = None

    @property
    def tier3_client(self) -> LLMClient:
        """延迟初始化 Tier-3 客户端"""
        if self._tier3_client is None:
            self._tier3_client = self.llm_factory.get_tier3()
        return self._tier3_client
```

**验收标准**:

- [ ] 所有引擎继承自 `Engine` 基类
- [ ] LLM 客户端正确实现懒加载

---

## 🟢 P2 - 增强功能（1-3个月）

### 7. 性能优化 [2周]

#### 7.1 并行 AST 解析

```python
# mapper.py
import asyncio
from concurrent.futures import ThreadPoolExecutor

async def map_repository_parallel(self, repo_path: Path) -> List[CodeSkeleton]:
    with ThreadPoolExecutor(max_workers=4) as executor:
        loop = asyncio.get_event_loop()
        tasks = [
            loop.run_in_executor(executor, self._parse_file, file)
            for file in self._discover_files(repo_path)
        ]
        return await asyncio.gather(*tasks)
```

#### 7.2 LLM 响应缓存

```python
# 新增: aegis/core/cache.py
import hashlib
import json
from pathlib import Path

class LLMResponseCache:
    def __init__(self, cache_dir: Path):
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(exist_ok=True)

    def get(self, prompt: str, model: str) -> Optional[str]:
        key = self._hash_key(prompt, model)
        cache_file = self.cache_dir / f"{key}.json"
        if cache_file.exists():
            return json.loads(cache_file.read_text())
        return None

    def set(self, prompt: str, model: str, response: str):
        key = self._hash_key(prompt, model)
        cache_file = self.cache_dir / f"{key}.json"
        cache_file.write_text(json.dumps(response))
```

**验收标准**:

- [ ] AST 解析速度提升 2-3x
- [ ] 相同提示词命中缓存

---

### 8. 监控与可观测性 [2周]

#### 8.1 指标收集

```python
# 新增: aegis/core/metrics.py
from dataclasses import dataclass
from typing import Dict

@dataclass
class Metrics:
    files_scanned: int = 0
    llm_api_calls: int = 0
    tokens_consumed: int = 0
    vulnerabilities_found: int = 0
    patches_applied: int = 0
    execution_time_seconds: float = 0.0

    def to_prometheus(self) -> str:
        """导出为 Prometheus 格式"""
        return f"""
# HELP aegis_files_scanned Total files scanned
# TYPE aegis_files_scanned counter
aegis_files_scanned {self.files_scanned}

# HELP aegis_llm_api_calls Total LLM API calls
# TYPE aegis_llm_api_calls counter
aegis_llm_api_calls {self.llm_api_calls}
...
"""
```

#### 8.2 进度仪表板

```bash
# 使用 Rich 库的 Live 显示
from rich.live import Live
from rich.table import Table

def create_dashboard(state: OrchestratorState) -> Table:
    table = Table(title="Aegis Box Dashboard")
    table.add_column("Step", style="cyan")
    table.add_column("Status", style="magenta")
    table.add_column("Progress", style="green")
    # ...
    return table
```

**验收标准**:

- [ ] 实时进度显示
- [ ] 可导出 Prometheus 指标

---

### 9. 多语言支持完善 [4周]

**当前状态**:

- ✅ Python
- ✅ JavaScript
- ✅ TypeScript
- ⏳ Rust (tree-sitter-rust 已声明)
- ⏳ Go
- ⏳ Java

**实现步骤**:

```python
# mapper.py 扩展
class Language(Enum):
    PYTHON = "python"
    JAVASCRIPT = "javascript"
    TYPESCRIPT = "typescript"
    RUST = "rust"  # 新增
    GO = "go"      # 新增
    JAVA = "java"  # 新增

def _init_parsers(self):
    if TREE_SITTER_AVAILABLE:
        self.parsers = {
            Language.PYTHON: tree_sitter.Parser(tspython.language()),
            Language.JAVASCRIPT: tree_sitter.Parser(tsjavascript.language()),
            Language.TYPESCRIPT: tree_sitter.Parser(tstypescript.language()),
            Language.RUST: tree_sitter.Parser(tsrust.language()),
            Language.GO: tree_sitter.Parser(tsgo.language()),
            Language.JAVA: tree_sitter.Parser(tsjava.language()),
        }
```

**验收标准**:

- [ ] 每种语言通过 10+ 个真实项目测试
- [ ] 压缩率 ≥ 60%

---

## 📈 成功指标

### 短期目标（1个月）

- [ ] 测试覆盖率 ≥ 80%
- [ ] Ruff 错误 < 50
- [ ] 核心功能（LLM 审计）完整实现
- [ ] 0 个 CRITICAL 安全漏洞

### 中期目标（3个月）

- [ ] API 文档完整
- [ ] 性能提升 2x
- [ ] 支持 6+ 编程语言
- [ ] 100+ GitHub stars

### 长期目标（6个月）

- [ ] Ouroboros Protocol 完整闭环
- [ ] CI/CD 集成插件
- [ ] 1000+ 活跃用户

---

## 📅 里程碑

| 日期       | 里程碑  | 交付物                            |
| ---------- | ------- | --------------------------------- |
| 2026-07-01 | P0 完成 | 测试通过 + LLM审计实现 + 安全修复 |
| 2026-07-15 | P1 完成 | 代码清理 + 文档完善 + 架构优化    |
| 2026-08-15 | P2 开始 | 性能优化 + 监控系统               |
| 2026-09-24 | v0.2.0  | 多语言支持 + 生产就绪             |

---

## 🤝 贡献者招募

这些任务适合外部贡献者（可进入 Hall of Fame）：

### 🥇 高价值任务

- [ ] 实现 Rust 语言支持
- [ ] 编写 CI/CD 集成指南
- [ ] 性能基准测试套件

### 🥈 中等价值任务

- [ ] 完善 API 文档
- [ ] Windows 兼容性测试
- [ ] 中文文档翻译

### 🥉 入门级任务

- [ ] 修复 Ruff 自动可修复问题
- [ ] 添加单元测试
- [ ] 改进错误消息

---

## 📝 每周检查清单

```markdown
## Week 1 (2026-06-24 - 2026-06-30)

- [ ] 修复测试环境
- [ ] 实现 LLM 审计核心功能（50%）
- [ ] 修复输入验证漏洞

## Week 2 (2026-07-01 - 2026-07-07)

- [ ] 完成 LLM 审计功能
- [ ] 修复路径遍历漏洞
- [ ] 添加日志脱敏
- [ ] P0 验收测试

## Week 3-4 (2026-07-08 - 2026-07-21)

- [ ] 清理 Ruff 问题
- [ ] 生成 API 文档
- [ ] 引入 Engine 抽象层
```

---

**🎯 目标：在 1 个月内将评分从 6.4/10 提升至 8.0/10**

---

_本计划基于 SELF_AUDIT_REPORT.md，每周更新进度_
