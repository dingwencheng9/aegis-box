# 🔍 Aegis Box 自审计深度分析报告

**审计日期**: 2026-06-23  
**审计方式**: Aegis 审计自身 (Bootstrapping)  
**分析师**: 资深架构师视角  
**审计对象**: Aegis Box v0.1.0 (Phase 1 骨架代码)

---

## 📋 执行总结

**审计时间**: 2026-06-23 21:22:25 - 21:22:32 (总计 7 秒)  
**执行模式**: 全自动模式 (--auto)  
**最终状态**: ✅ 形式上成功，但使用模拟数据

### 🚨 核心发现

**这是 Phase 1 的骨架代码，核心功能尚未实现**

证据：

1. ⚡ 执行速度异常快 (7秒完成4个阶段)
2. 📊 输出模拟数据 (硬编码的测试值)
3. 🔌 缺少实际 LLM API 调用
4. 📄 未生成真实的架构报告

---

## 🏗️ 架构质量分析

### ✅ Phase 1 已完成的优秀设计

#### 1. **项目结构** ⭐⭐⭐⭐⭐ (5/5)

```
aegis/
├── cli.py              # CLI 入口 (17KB) - 完整
├── core/               # 核心模块
│   ├── llm.py         # LLM 抽象 (20KB) - 架构完整，待实现调用
│   └── rate_limiter.py # 速率限制 (6KB) - 完整
├── engines/            # 执行引擎
│   ├── sweeper.py     # 资产清道夫 (9KB) - 骨架
│   ├── mapper.py      # AST 提取 (20KB) - 部分实现
│   ├── reducer.py     # 架构审计 (23KB) - 骨架
│   ├── patcher.py     # 智能补丁 (13KB) - 骨架
│   ├── context_injector.py # 上下文注入 (16KB) - 骨架
│   └── orchestrator.py # 流程编排 (18KB) - 空壳
└── utils/              # 工具模块
    ├── diff_parser.py # SEARCH/REPLACE 解析 (17KB) - 完整
    └── git_sandbox.py # Git 沙盒 (14KB) - 完整
```

**优点**:

- ✅ 清晰的分层架构 (CLI → Engines → Core → Utils)
- ✅ 高内聚低耦合的模块划分
- ✅ 遵循单一职责原则
- ✅ 依赖注入友好

---

### 🚨 P0 级架构异味（Critical - 必须修复）

#### 1. **空壳编排器 - 核心功能缺失**

**位置**: `aegis/engines/orchestrator.py:263, 289, 316, 347`

**代码证据**:

```python
# Line 263
async def _step_sweep(self):
    # TODO: 实际实现需要调用 AssetSweeper
    await asyncio.sleep(1)  # ❌ 模拟执行
    return {"files_scanned": 1000}  # ❌ 硬编码数据

# Line 289
async def _step_reduce(self):
    # TODO: 实际实现需要调用 ArchitectureReducer
    await asyncio.sleep(2)
    return {"vulnerabilities_found": 3}  # ❌ 假数据

# Line 316
async def _step_patch(self):
    # TODO: 实际实现需要调用 SmartPatcher
    await asyncio.sleep(3)
    return {"vulnerabilities_fixed": 2}  # ❌ 假数据

# Line 347
async def _step_context_sync(self):
    # TODO: 实际实现需要调用 ContextInjector
    await asyncio.sleep(1)
    return {"injected": True}  # ❌ 假数据
```

**架构异味分类**:

- 🔴 **Facade Pattern 误用** - 编排器只是空壳
- 🔴 **Mock 污染生产代码** - 测试数据混入正式代码
- 🔴 **职责缺失** - 核心职责完全未实现

**影响评估**:

- **严重度**: 🔴 Critical
- **用户影响**: 用户以为完成了审计，实际什么都没做
- **安全风险**: 可能导致真实漏洞被忽略

**修复建议**:

```python
async def _step_reduce(self):
    """架构审计步骤 - 真实实现"""
    from aegis.engines.reducer import ArchitectureReducer

    # 1. 创建 LLM 客户端
    tier1 = self._create_llm_client(self.config.llm.tier1_fast)
    tier2 = self._create_llm_client(self.config.llm.tier2_reasoning)

    # 2. 创建审计器
    reducer = ArchitectureReducer(tier1, tier2, self.config)

    # 3. 执行审计
    report = await reducer.run(self.project_root)

    # 4. 保存报告
    report_path = self.session_dir / "architecture_report.md"
    report_path.write_text(report.to_markdown())

    return report.to_dict()
```

---

#### 2. **AST 解析器依赖缺失**

**位置**: `aegis/engines/mapper.py:427`

**代码证据**:

```python
def _extract_js_ts_ast(self, file_path: str) -> Optional[FileASTSkeleton]:
    """提取 JS/TS 的 AST 骨架"""
    # TODO: 实现 JS/TS 的 AST 提取逻辑
    return None  # ❌ 完全未实现
```

**根本原因**:

- tree-sitter 无法在 Python 3.14 freethreaded 上编译
- 编译错误：`call to undeclared function '_Py_IsOwnedByCurrentThread'`

**架构异味分类**:

- 🔴 **部分实现 (Partially Implemented)**
- 🔴 **依赖地狱** - 关键依赖无法安装
- 🔴 **单点故障** - 整个 Mapper 不可用

**影响评估**:

- **严重度**: 🔴 Critical
- **影响范围**: JS/TS/Python 项目都无法审计
- **阻塞**: Phase 2 开发被阻塞

**修复建议** (3 个方案):

**方案 A: 正则表达式降级** (快速，推荐用于 MVP)

```python
def _extract_ast_regex_fallback(self, file_path: str, lang: str) -> FileASTSkeleton:
    """使用正则表达式提取代码结构（降级方案）"""
    content = Path(file_path).read_text()

    if lang == 'python':
        functions = re.findall(r'^def\s+(\w+)\s*\([^)]*\):', content, re.MULTILINE)
        classes = re.findall(r'^class\s+(\w+)', content, re.MULTILINE)
        imports = re.findall(r'^(?:from\s+[\w.]+\s+)?import\s+([\w,\s]+)', content, re.MULTILINE)
    elif lang in ['javascript', 'typescript']:
        functions = re.findall(r'function\s+(\w+)|const\s+(\w+)\s*=.*?=>', content)
        classes = re.findall(r'class\s+(\w+)', content)
        imports = re.findall(r'import.*?from\s+["\']([^"\']+)["\']', content)

    return FileASTSkeleton(
        file=file_path,
        functions=[f for f in functions if f],
        classes=classes,
        imports=imports
    )
```

**方案 B: 切换到标准 Python 3.13** (稳定，推荐)

```bash
# 重建虚拟环境
rm -rf .venv
python3.13 -m venv .venv
.venv/bin/pip install -e ".[dev]"
```

**方案 C: 使用 AST 模块 (Python 内置)** (仅限 Python)

```python
import ast

def _extract_python_ast_builtin(self, file_path: str) -> FileASTSkeleton:
    """使用内置 ast 模块解析 Python"""
    with open(file_path) as f:
        tree = ast.parse(f.read())

    functions = [n.name for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)]
    classes = [n.name for n in ast.walk(tree) if isinstance(n, ast.ClassDef)]
    imports = []
    for n in ast.walk(tree):
        if isinstance(n, ast.Import):
            imports.extend(alias.name for alias in n.names)
        elif isinstance(n, ast.ImportFrom):
            imports.append(n.module)

    return FileASTSkeleton(file=file_path, functions=functions, classes=classes, imports=imports)
```

---

#### 3. **LLM 客户端 - 缺少验证**

**位置**: `aegis/core/llm.py`

**问题**: 虽然架构完整，但需要验证实际调用是否工作

**验证清单**:

```python
# ✅ 已有的架构
- 熔断器机制
- 指数退避重试
- 速率限制集成
- 结构化输出支持 (Pydantic)

# ❌ 需要验证
- 实际 API 调用是否成功
- Token 统计是否准确
- 错误处理是否完善
- 超时机制是否生效
```

**建议添加集成测试**:

```python
# tests/integration/test_llm_client.py
async def test_anthropic_real_call():
    """测试真实的 Anthropic API 调用"""
    config = ModelTierConfig(
        provider="anthropic",
        model="claude-haiku-4-5-20251001",
        api_key_env_var="ANTHROPIC_API_KEY",
        endpoint="https://cdn1.yunyi.yun/claude"
    )

    client = LLMClient(config, rate_limiter)
    response = await client.chat("请回复：测试成功")

    assert "测试成功" in response
    assert client._stats["success_calls"] == 1
    assert client._stats["total_tokens"] > 0
```

---

### 🟡 P1 级架构异味（High - 应该修复）

#### 4. **reducer.py - 上帝类反模式**

**位置**: `aegis/engines/reducer.py`

**问题**: 一个文件承担了太多职责

```python
# 当前 reducer.py 包含：
1. ✅ 数据模型定义 (Vuln, FileAnalysis, ArchitecturePanorama)
2. ✅ 业务逻辑 (ArchitectureReducer 类)
3. ✅ Prompt 模板 (长篇 Prompt 字符串)
4. ✅ 报告生成 (to_markdown 方法)
5. ✅ TODO 降采样逻辑
6. ✅ 统计汇总逻辑

# 问题：23KB 的单文件，职责混杂
```

**架构异味分类**:

- 🟡 **God Class (上帝类)** - 做太多事
- 🟡 **SRP 违反** - 单一职责原则违反
- 🟡 **低内聚** - 不相关的逻辑混在一起

**内聚度评分**: ⭐⭐ (2/5)

**影响**:

- 🟡 **Medium**: 代码难以维护
- 🟡 测试困难 (需要 mock 太多东西)
- 🟡 扩展困难 (添加新功能需要修改巨大文件)

**重构建议**:

```
aegis/
├── models/
│   ├── __init__.py
│   ├── vulnerability.py        # Vuln, VulnSeverity
│   ├── file_analysis.py        # FileAnalysis
│   └── architecture_report.py  # ArchitecturePanorama
├── engines/
│   ├── reducer.py              # 只保留 ArchitectureReducer 逻辑
│   └── reporters/
│       ├── __init__.py
│       ├── markdown.py         # MarkdownReporter
│       └── json.py             # JSONReporter
├── prompts/
│   ├── __init__.py
│   ├── tier1_file_analysis.py  # TIER1_PROMPT
│   └── tier2_architecture.py   # TIER2_PROMPT
└── utils/
    ├── sampling.py             # TODO 降采样
    └── statistics.py           # 统计汇总
```

---

#### 5. **CLI 与引擎紧耦合**

**位置**: `aegis/cli.py`

**问题**: CLI 直接创建引擎实例

```python
# 当前实现（紧耦合）
from aegis.engines.orchestrator import Orchestrator

@app.command()
def run():
    orchestrator = Orchestrator()  # ❌ 硬编码创建
    orchestrator.run()
```

**架构异味分类**:

- 🟡 **Tight Coupling (紧耦合)**
- 🟡 **可测试性差** - 无法 mock Orchestrator
- 🟡 **扩展性差** - 添加新引擎需要改 CLI

**耦合度评分**: ⭐⭐⭐ (3/5)

**重构建议 - 依赖注入**:

```python
# 创建服务容器
class ServiceContainer:
    """DI 容器"""
    def __init__(self, config: AegisConfig):
        self.config = config
        self.rate_limiter = self._create_rate_limiter()

    def _create_rate_limiter(self) -> RateLimiter:
        return RateLimiter(self.config.rate_limit)

    def create_llm_client(self, tier_config: ModelTierConfig) -> LLMClient:
        return LLMClient(tier_config, self.rate_limiter)

    def create_orchestrator(self) -> Orchestrator:
        return Orchestrator(
            config=self.config,
            container=self
        )

# CLI 使用容器
@app.command()
def run():
    config = load_config()
    container = ServiceContainer(config)
    orchestrator = container.create_orchestrator()
    asyncio.run(orchestrator.run())
```

---

#### 6. **错误处理不一致**

**位置**: 多个文件

**问题**: 3 种不同的错误处理策略

```python
# 策略 1: 返回 None (mapper.py)
def extract_ast(self, file):
    try:
        return parse(file)
    except Exception:
        return None  # ❌ 静默失败

# 策略 2: 抛出异常 (reducer.py)
def reduce(self, files):
    if not files:
        raise ValueError("No files")  # ✅ 明确失败

# 策略 3: 只记录日志 (orchestrator.py)
def run(self):
    try:
        self.sweep()
    except Exception as e:
        logger.error(f"Failed: {e}")  # ❌ 不传播错误
```

**架构异味分类**:

- 🟡 **Inconsistent Error Handling**
- 🟡 **Silent Failures** - 错误被吞掉
- 🟡 **缺少错误传播链**

**统一建议**:

```python
# 1. 定义异常层次
class AegisError(Exception):
    """Aegis 基础异常"""
    pass

class AegisEngineError(AegisError):
    """引擎异常"""
    pass

class AegisParserError(AegisError):
    """解析异常"""
    pass

# 2. 统一策略
# - 底层：抛出具体异常
# - 中层：传播或转换
# - 顶层：捕获、记录、向用户报告

# 示例
def extract_ast(self, file):
    try:
        return parse(file)
    except SyntaxError as e:
        raise AegisParserError(f"Failed to parse {file}: {e}") from e
```

---

### 🟢 P2 级架构异味（Medium - 可优化）

#### 7. **配置验证缺失**

**位置**: `aegis/cli.py`

**问题**: 配置加载后不验证 API Key

```python
def load_config():
    config = AegisConfig(**yaml.safe_load(...))
    # ❌ 没有验证 ANTHROPIC_API_KEY 是否真的存在
    return config
```

**建议**:

```python
def validate_config(config: AegisConfig) -> List[str]:
    """验证配置"""
    errors = []

    # 验证 API Keys
    for tier_name, tier in [
        ("Tier1", config.llm.tier1_fast),
        ("Tier2", config.llm.tier2_reasoning),
        ("Tier3", config.llm.tier3_patching),
    ]:
        if not os.getenv(tier.api_key_env_var):
            errors.append(f"{tier_name}: 缺少环境变量 {tier.api_key_env_var}")

    return errors

@app.command()
def config_validate():
    """验证配置"""
    config = load_config()
    errors = validate_config(config)

    if errors:
        for error in errors:
            console.print(f"❌ {error}", style="red")
        raise typer.Exit(1)
    else:
        console.print("✅ 配置验证通过", style="green")
```

---

#### 8. **缺少并发控制和进度反馈**

**位置**: `aegis/engines/reducer.py`

**观察**:

- ✅ 使用了 asyncio
- ⚠️ 但没有 Semaphore 限制并发
- ⚠️ 没有进度条

**建议**:

```python
from rich.progress import Progress, SpinnerColumn, TimeElapsedColumn

async def run_tier1_with_progress(self, files: List[str]):
    """带进度条的 Tier1 并发执行"""
    semaphore = asyncio.Semaphore(10)  # 限制并发

    async def process(file, task_id):
        async with semaphore:
            result = await self.tier1.chat(...)
            progress.update(task_id, advance=1)
            return result

    with Progress(
        SpinnerColumn(),
        *Progress.get_default_columns(),
        TimeElapsedColumn(),
    ) as progress:
        task = progress.add_task(
            "[cyan]Tier1 探伤中...",
            total=len(files)
        )

        tasks = [process(f, task) for f in files]
        return await asyncio.gather(*tasks)
```

---

## 📊 内聚度/耦合度综合评分

| 模块                            | 内聚度           | 耦合度           | 综合   | 评价                       |
| ------------------------------- | ---------------- | ---------------- | ------ | -------------------------- |
| **cli.py**                      | ⭐⭐⭐⭐ (4/5)   | ⭐⭐⭐ (3/5)     | **B+** | CLI 职责清晰，但与引擎耦合 |
| **core/llm.py**                 | ⭐⭐⭐⭐⭐ (5/5) | ⭐⭐⭐⭐ (4/5)   | **A**  | 架构优秀，依赖注入良好     |
| **core/rate_limiter.py**        | ⭐⭐⭐⭐⭐ (5/5) | ⭐⭐⭐⭐⭐ (5/5) | **A+** | 完美的单一职责             |
| **engines/sweeper.py**          | ⭐⭐⭐⭐ (4/5)   | ⭐⭐⭐⭐ (4/5)   | **A-** | 职责清晰                   |
| **engines/mapper.py**           | ⭐⭐⭐⭐ (4/5)   | ⭐⭐⭐ (3/5)     | **B+** | 职责明确，依赖 tree-sitter |
| **engines/reducer.py**          | ⭐⭐ (2/5)       | ⭐⭐⭐ (3/5)     | **C**  | ❌ 上帝类                  |
| **engines/patcher.py**          | ⭐⭐⭐⭐ (4/5)   | ⭐⭐⭐ (3/5)     | **B**  | 职责清晰                   |
| **engines/context_injector.py** | ⭐⭐⭐⭐ (4/5)   | ⭐⭐⭐⭐ (4/5)   | **A-** | 职责明确                   |
| **engines/orchestrator.py**     | ⭐⭐ (2/5)       | ⭐⭐ (2/5)       | **D**  | ❌ 空壳实现                |
| **utils/diff_parser.py**        | ⭐⭐⭐⭐⭐ (5/5) | ⭐⭐⭐⭐⭐ (5/5) | **A+** | 完美工具类                 |
| **utils/git_sandbox.py**        | ⭐⭐⭐⭐ (4/5)   | ⭐⭐⭐⭐ (4/5)   | **A-** | 封装良好                   |

### 平均评分

- **整体内聚度**: ⭐⭐⭐⭐ (3.8/5)
- **整体耦合度**: ⭐⭐⭐ (3.5/5)
- **综合评分**: **B+** (82/100)

---

## 🎯 优先修复路线图

### Phase 2 - 核心功能实现 (2-3 周)

**Week 1: 解除阻塞器**

```
Day 1-2: 修复 AST 解析器 (P0-2)
  - 方案 A: 切换到 Python 3.13
  - 方案 B: 实现正则降级方案

Day 3-5: 实现 LLM 客户端真实调用 (P0-3)
  - 验证 Anthropic API 调用
  - 验证 Zhipu API 调用
  - 添加集成测试

Day 6-7: 实现 Orchestrator 真实编排 (P0-1)
  - 连接各个引擎
  - 移除 mock 数据
  - 端到端测试
```

**Week 2: 架构重构**

```
Day 1-3: 重构 reducer.py (P1-4)
  - 拆分模型到 models/
  - 拆分报告器到 reporters/
  - 拆分 Prompt 到 prompts/

Day 4-5: 实现依赖注入 (P1-5)
  - 创建 ServiceContainer
  - 重构 CLI
  - 添加单元测试

Day 6-7: 统一错误处理 (P1-6)
  - 定义异常层次
  - 统一错误策略
  - 添加错误恢复机制
```

**Week 3: 完善与优化**

```
Day 1-2: 配置验证 (P2-7)
  - 实现 config validate 命令
  - 添加启动检查

Day 3-4: 并发优化 (P2-8)
  - 添加 Semaphore 限制
  - 集成 rich 进度条

Day 5-7: 集成测试与文档
  - 端到端测试
  - 性能测试
  - 更新文档
```

---

## 📈 长期建议

### 1. 引入设计模式

**Strategy Pattern** - 支持多种 AST 解析策略

```python
class ASTParserStrategy(ABC):
    @abstractmethod
    def parse(self, file_path: str) -> FileASTSkeleton:
        pass

class TreeSitterParser(ASTParserStrategy):
    def parse(self, file_path: str):
        # 使用 tree-sitter
        ...

class RegexParser(ASTParserStrategy):
    def parse(self, file_path: str):
        # 使用正则表达式
        ...

class ASTMapper:
    def __init__(self, strategy: ASTParserStrategy):
        self.strategy = strategy
```

### 2. 添加可观测性

```python
# 集成 OpenTelemetry
from opentelemetry import trace

tracer = trace.get_tracer(__name__)

async def run(self):
    with tracer.start_as_current_span("aegis.run"):
        with tracer.start_as_current_span("aegis.sweep"):
            await self.sweep()
        with tracer.start_as_current_span("aegis.reduce"):
            await self.reduce()
```

### 3. 性能监控

```python
# 添加性能指标
class Metrics:
    def __init__(self):
        self.counters = {}
        self.timers = {}

    def inc(self, name: str, value: int = 1):
        self.counters[name] = self.counters.get(name, 0) + value

    @contextmanager
    def timer(self, name: str):
        start = time.time()
        yield
        elapsed = time.time() - start
        self.timers[name] = elapsed
```

---

## 🏆 总结

### Aegis 对自己的评价

如果 Aegis 的大模型真的审计了自己，它会发现：

**✅ 优秀的架构基础**

- 清晰的分层和模块划分
- 优秀的工具类设计 (diff_parser, git_sandbox)
- 完善的 LLM 抽象层

**🚨 关键的实现缺口**

- P0-1: Orchestrator 是空壳
- P0-2: AST 解析器无法工作
- P0-3: LLM 调用待验证

**🎯 架构改进方向**

- P1-4: 拆分 reducer.py 上帝类
- P1-5: 引入依赖注入解耦
- P1-6: 统一错误处理策略

### 最终评分

**当前状态**: Phase 1 骨架 (30% 完成度)
**架构质量**: B+ (82/100)
**可维护性**: B (75/100)
**可扩展性**: A- (85/100)

**推荐行动**:

1. 🔥 立即修复 3 个 P0 问题
2. 📅 2 周内完成 Phase 2 核心功能
3. 🔄 持续重构 reducer.py 和依赖注入

---

**报告生成时间**: 2026-06-23 21:30  
**分析方法**: 代码审查 + TODO 标记扫描 + 架构模式识别  
**审计工具**: Aegis Box v0.1.0 (骨架) + 人工深度分析
