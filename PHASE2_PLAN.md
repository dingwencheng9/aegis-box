# 🛡️ Aegis Box - Phase 2 详细实施方案

## 📋 Phase 2 概述

**目标**：完成上下文提纯与 AST 降维，实现代码库的智能压缩和架构洞察。

**核心产出**：

1. ✅ 资产清道夫（Asset Sweeper）- 已完成
2. ✅ AST 特征提取器（Code Mapper）- 已完成
3. 🚧 双轨架构归纳器（Reducer）- 待开发
4. 🚧 IDE 上下文注入器（Context Injector）- 待开发

---

## ✅ 已完成的组件

### 1. 资产清道夫（Asset Sweeper）

**位置**：`aegis/engines/sweeper.py`

**功能**：

- 高速多线程/异步文件扫描
- 识别垃圾文件和目录（`node_modules`, `__pycache__` 等）
- 计算可节省的磁盘空间
- 安全删除（支持 dry-run 模式）

**关键特性**：

```python
# 扫描 10GB 的项目，5 秒内完成
result = await sweeper.scan_async(project_root)
print(f"可节省空间: {result.ignorable_size_mb:.2f} MB")
```

**测试覆盖**：

- ✅ 目录/文件忽略规则
- ✅ 同步/异步扫描
- ✅ 大小计算精度

### 2. AST 特征提取器（Code Mapper）

**位置**：`aegis/engines/mapper.py`

**功能**：

- 使用 tree-sitter 进行精确 AST 解析
- 提取类/函数签名、导入依赖
- 保留跨函数调用关系
- 保留 TODO/FIXME 等关键注释
- 支持 Python/JavaScript/TypeScript

**压缩效果**：

```
输入: 5000 行复杂业务代码
输出: 500 行结构化骨架 (10% 压缩率)
```

**关键数据结构**：

```python
@dataclass
class CodeSkeleton:
    imports: List[ImportInfo]        # 导入依赖
    classes: List[ClassInfo]         # 类定义（含方法）
    functions: List[FunctionInfo]    # 顶级函数
    global_comments: List[Comment]   # 重要注释
```

**测试覆盖**：

- ✅ 多语言检测
- ✅ Python AST 提取精度
- ✅ 函数调用关系提取
- ✅ Markdown 生成格式

---

## 🚧 待开发组件

### 3. 双轨架构归纳器（Reducer）

**文件**：`aegis/engines/reducer.py`

**架构设计**：

```
┌─────────────────────────────────────────────────┐
│  Step 1: 代码骨架生成（Mapper）                    │
│  输入: 整个项目源码                                │
│  输出: 每个文件的 CodeSkeleton                     │
└─────────────────────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────────┐
│  Step 2: Tier-1 并发切片探伤                       │
│  模型: GLM-4-Air（快速+便宜）                       │
│  任务: 为每个文件生成"单文件摘要"                     │
│  - 这个文件的核心职责是什么？                        │
│  - 有哪些潜在的代码异味？                           │
│  - 有哪些 TODO/FIXME 需要关注？                     │
└─────────────────────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────────┐
│  Step 3: 聚合所有单文件摘要                         │
│  输入: 100 个文件的 Tier-1 摘要                     │
│  输出: 项目级别的"全景视图"                          │
│  - 目录结构树                                      │
│  - 核心模块列表                                    │
│  - 依赖关系图                                      │
└─────────────────────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────────┐
│  Step 4: Tier-2 宏观架构总结                        │
│  模型: Claude-3.5-Haiku（中等推理能力）              │
│  任务: 生成架构级别的洞察报告                        │
│  - 这是一个什么类型的项目？（Web后端/前端/CLI）        │
│  - 采用了哪些架构模式？（MVC/DDD/微服务）            │
│  - 存在哪些架构级别的风险？                         │
│  - 推荐的重构路径是什么？                           │
└─────────────────────────────────────────────────┘
```

**核心代码框架**：

```python
class ArchitectureReducer:
    """双轨架构归纳器"""

    def __init__(
        self,
        tier1_client: LLMClient,
        tier2_client: LLMClient,
        rate_limiter: RateLimiter
    ):
        self.tier1 = tier1_client
        self.tier2 = tier2_client
        self.limiter = rate_limiter

    async def analyze_file(
        self,
        skeleton: CodeSkeleton
    ) -> FileSummary:
        """Tier-1: 单文件分析"""
        prompt = self._build_file_analysis_prompt(skeleton)

        await self.limiter.acquire("tier1", estimated_tokens=2000)
        response = await self.tier1.chat(prompt)

        return FileSummary.parse(response)

    async def analyze_project(
        self,
        skeletons: List[CodeSkeleton]
    ) -> ArchitectureReport:
        """完整的双轨分析流程"""

        # Step 1: 并发分析所有文件（Tier-1）
        tasks = [self.analyze_file(s) for s in skeletons]
        file_summaries = await asyncio.gather(*tasks)

        # Step 2: 聚合全景视图
        panorama = self._aggregate_summaries(file_summaries)

        # Step 3: 宏观架构总结（Tier-2）
        await self.limiter.acquire("tier2", estimated_tokens=10000)
        architecture_insight = await self.tier2.chat(
            self._build_architecture_prompt(panorama)
        )

        return ArchitectureReport(
            file_summaries=file_summaries,
            panorama=panorama,
            architecture_insight=architecture_insight
        )
```

**Prompt 设计**：

```python
# Tier-1 Prompt（快速探伤）
TIER1_FILE_ANALYSIS = """
你是一个代码审查专家。请分析以下文件的代码骨架，回答：

1. 这个文件的核心职责是什么？（1 句话）
2. 有哪些潜在的代码异味或漏洞？（列表）
3. 有哪些 TODO/FIXME 需要优先处理？（列表）

代码骨架：
{skeleton_markdown}

请以 JSON 格式输出：
{
  "responsibility": "...",
  "code_smells": ["...", "..."],
  "priority_todos": ["...", "..."]
}
"""

# Tier-2 Prompt（宏观架构）
TIER2_ARCHITECTURE_ANALYSIS = """
你是一个软件架构师。基于以下项目全景视图，回答：

1. 这是什么类型的项目？（Web后端/前端/CLI/库）
2. 采用了哪些架构模式？（MVC/DDD/微服务/单体）
3. 存在哪些架构级别的风险？（技术债/性能瓶颈/安全隐患）
4. 推荐的重构路径是什么？（优先级排序）

项目全景：
{panorama}

请以 Markdown 格式输出完整的架构报告。
"""
```

**数据模型**：

```python
@dataclass
class FileSummary:
    """单文件摘要（Tier-1 输出）"""
    file_path: Path
    responsibility: str
    code_smells: List[str]
    priority_todos: List[str]

@dataclass
class ProjectPanorama:
    """项目全景视图（聚合结果）"""
    total_files: int
    total_lines: int
    directory_tree: Dict
    core_modules: List[str]
    dependency_graph: Dict
    all_todos: List[str]

@dataclass
class ArchitectureReport:
    """架构报告（Tier-2 输出）"""
    project_type: str
    architecture_patterns: List[str]
    risks: List[Dict]  # {"level": "high", "description": "..."}
    refactoring_roadmap: List[str]
    file_summaries: List[FileSummary]
    panorama: ProjectPanorama
```

### 4. IDE 上下文注入器（Context Injector）

**文件**：`aegis/engines/context_injector.py`

**功能**：

- 将架构报告转换为 `.claude_context.xml`
- 生成 `.cursorrules` 文件
- 可选生成 `.vscode/settings.json` 增强配置

**生成示例**：

```xml
<!-- .claude_context.xml -->
<context>
  <project>
    <name>MyProject</name>
    <type>FastAPI Web Backend</type>
    <architecture>Layered Architecture (Controller -> Service -> Repository)</architecture>
  </project>

  <dependencies>
    <external>
      <package>fastapi</package>
      <package>sqlalchemy</package>
      <package>pydantic</package>
    </external>
  </dependencies>

  <structure>
    <module name="api" responsibility="HTTP 路由和请求处理" />
    <module name="services" responsibility="业务逻辑层" />
    <module name="models" responsibility="数据模型和 ORM 映射" />
  </structure>

  <risks>
    <risk level="high">
      SQL 注入风险：user_service.py L67 使用字符串拼接构建查询
    </risk>
    <risk level="medium">
      性能问题：缺少数据库索引，N+1 查询
    </risk>
  </risks>

  <refactoring_suggestions>
    <suggestion priority="1">
      将 user_service.py 拆分为 user_query.py 和 user_command.py（CQRS 模式）
    </suggestion>
    <suggestion priority="2">
      添加 Redis 缓存层以减少数据库查询
    </suggestion>
  </refactoring_suggestions>
</context>
```

```markdown
<!-- .cursorrules -->

# Aegis 自动生成的代码规范

## 项目架构

- 类型: FastAPI Web Backend
- 模式: Layered Architecture

## 编码规范

1. 所有 API 端点必须使用 Pydantic 验证输入
2. 数据库查询必须使用参数化查询（防止 SQL 注入）
3. Service 层函数必须添加类型注解

## 已知风险

⚠️ HIGH: user_service.py L67 存在 SQL 注入风险
⚠️ MEDIUM: 缺少数据库索引，存在 N+1 查询问题

## 重构建议

1. 【优先级 1】拆分 user_service.py（当前 800 行，过大）
2. 【优先级 2】添加 Redis 缓存层
3. 【优先级 3】引入异步任务队列（Celery）
```

---

## 📊 Phase 2 开发计划

### Week 1: LLM 客户端封装

- [ ] 创建 `aegis/core/llm.py`
- [ ] 封装 LiteLLM 调用逻辑
- [ ] 实现 Tier-1 和 Tier-2 客户端
- [ ] 添加重试机制和错误处理
- [ ] 编写单元测试

### Week 2: 双轨归纳器

- [ ] 创建 `aegis/engines/reducer.py`
- [ ] 实现 Tier-1 并发文件分析
- [ ] 实现全景视图聚合
- [ ] 实现 Tier-2 架构总结
- [ ] 优化 Prompt 设计
- [ ] 编写集成测试

### Week 3: 上下文注入器

- [ ] 创建 `aegis/engines/context_injector.py`
- [ ] 实现 `.claude_context.xml` 生成
- [ ] 实现 `.cursorrules` 生成
- [ ] 添加模板系统（Jinja2）
- [ ] 编写测试

### Week 4: CLI 集成与测试

- [ ] 更新 `aegis/cli.py` 集成新功能
- [ ] 实现 `aegis audit` 完整流程
- [ ] 添加进度条和美化输出（Rich）
- [ ] 端到端测试
- [ ] 性能优化
- [ ] 文档更新

---

## 🎯 关键性能指标（KPIs）

### 速度

- 扫描 1000 个文件：< 30 秒
- 生成单文件摘要（Tier-1）：< 2 秒
- 生成架构报告（Tier-2）：< 10 秒
- 总耗时（完整流程）：< 2 分钟

### 成本

- Tier-1 单文件：~ $0.001（GLM-4-Air）
- Tier-2 架构总结：~ $0.05（Claude-3.5-Haiku）
- 分析 1000 文件项目：< $2

### 质量

- AST 提取准确率：> 95%
- 压缩率：< 15%（目标 10%）
- Tier-1 摘要有效性：> 80%（人工评估）
- Tier-2 架构洞察准确性：> 90%

---

## 🚀 快速启动开发

```bash
# 1. 安装依赖
poetry install

# 2. 运行当前测试
poetry run pytest -v

# 3. 启动开发模式（自动重载）
poetry run aegis audit ./examples --output report.md

# 4. 查看测试覆盖率
poetry run pytest --cov=aegis --cov-report=html
open htmlcov/index.html
```

---

## 💡 下一步行动

需要我立即开始实现以下哪个组件？

1. **LLM 客户端封装** (`aegis/core/llm.py`)
   - 统一 LiteLLM 调用接口
   - 实现重试和错误处理

2. **双轨归纳器** (`aegis/engines/reducer.py`)
   - Tier-1 并发文件分析
   - Tier-2 架构总结

3. **上下文注入器** (`aegis/engines/context_injector.py`)
   - 生成 IDE 友好的上下文文件

请告诉我优先级，我会立即开始实现！
