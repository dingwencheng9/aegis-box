# 🤝 Contributing to Aegis Box

欢迎贡献！我们非常欢迎社区贡献者帮助 Aegis Box 变得更好。

---

## 🎯 最受欢迎的贡献

### 1. 新增 AST 语言支持 🌟

**最受欢迎！** 如果你想为 Aegis 添加新的编程语言支持（Rust、Go、Java 等），这是最有价值的贡献。

#### 实现步骤

**Step 1: 安装对应的 tree-sitter 解析器**

```bash
# 以 Rust 为例
pip install tree-sitter-rust
```

**Step 2: 修改 `aegis/engines/mapper.py`**

找到 `FeatureMapper` 类，添加新语言的解析器：

```python
# 文件: aegis/engines/mapper.py
# 位置: class FeatureMapper

def _get_parser(self, language: str):
    """获取语言解析器"""

    parsers = {
        "python": tree_sitter_python,
        "typescript": tree_sitter_typescript,
        "javascript": tree_sitter_javascript,
        # 👇 在这里添加新语言
        "rust": tree_sitter_rust,
        "go": tree_sitter_go,
        "java": tree_sitter_java,
    }

    return parsers.get(language)
```

**Step 3: 添加语言特定的 AST 查询**

在 `aegis/engines/mapper.py` 中添加查询模式：

```python
# 文件: aegis/engines/mapper.py
# 位置: def _extract_features()

# Rust 示例
if language == "rust":
    queries = """
    (function_item name: (identifier) @function.name)
    (struct_item name: (type_identifier) @class.name)
    (impl_item trait: (type_identifier) @trait.name)
    (use_declaration argument: (scoped_identifier) @import)
    """

# Go 示例
elif language == "go":
    queries = """
    (function_declaration name: (identifier) @function.name)
    (type_declaration (type_spec name: (type_identifier) @class.name))
    (import_declaration (import_spec path: (interpreted_string_literal) @import))
    """
```

**Step 4: 添加文件扩展名映射**

```python
# 文件: aegis/engines/mapper.py
# 位置: def _detect_language()

EXTENSION_MAP = {
    ".py": "python",
    ".ts": "typescript",
    ".js": "javascript",
    # 👇 添加新扩展名
    ".rs": "rust",
    ".go": "go",
    ".java": "java",
}
```

**Step 5: 添加测试**

```python
# 文件: tests/test_mapper.py

def test_rust_ast_extraction():
    """测试 Rust AST 提取"""
    code = '''
    fn calculate_sum(a: i32, b: i32) -> i32 {
        a + b
    }

    struct User {
        name: String,
        age: u32,
    }
    '''

    mapper = FeatureMapper(repo_path=tmp_path)
    features = mapper.extract_features(code, "rust")

    assert "calculate_sum" in features["functions"]
    assert "User" in features["classes"]
```

**Step 6: 更新文档**

在 `README.md` 中更新支持的语言列表：

```markdown
## 支持的语言

- ✅ Python
- ✅ TypeScript / JavaScript
- ✅ Rust (感谢 @your-username)
- ✅ Go (感谢 @your-username)
```

---

### 2. 新增 LLM 提供商支持

**Step 1: 修改 `aegis/core/llm.py`**

```python
# 文件: aegis/core/llm.py

async def create_client(provider: str, model: str, api_key: str):
    """创建 LLM 客户端"""

    if provider == "anthropic":
        return AnthropicClient(model, api_key)
    elif provider == "openai":
        return OpenAIClient(model, api_key)
    # 👇 添加新提供商
    elif provider == "gemini":
        return GeminiClient(model, api_key)
    elif provider == "ollama":
        return OllamaClient(model)  # 本地，无需 API key
```

**Step 2: 实现客户端类**

```python
# 文件: aegis/core/llm.py

class GeminiClient(BaseLLMClient):
    """Google Gemini 客户端"""

    async def complete(self, prompt: str) -> str:
        # 实现 Gemini API 调用
        pass
```

**Step 3: 添加配置示例**

在 `aegis.yaml` 中添加示例配置。

---

### 3. 新增 IDE 集成支持

当前支持：Cursor、Claude Code

**欢迎添加**：VS Code、JetBrains、Vim 等

**修改文件**：`aegis/engines/context_injector.py`

```python
# 添加新的 IDE 格式
def _generate_vscode_format(self, report):
    """生成 VS Code 格式"""
    pass
```

---

## 🛠️ 开发环境设置

### 1. Fork 并克隆仓库

```bash
git clone https://github.com/your-username/aegis-box.git
cd aegis-box
```

### 2. 安装依赖

```bash
# 使用 uv（推荐）
uv venv
source .venv/bin/activate
uv pip install -e ".[dev]"

# 或使用 pip
python -m venv venv
source venv/bin/activate
pip install -e ".[dev]"
```

### 3. 运行测试

```bash
# 运行所有测试
pytest tests/ -v

# 运行特定测试
pytest tests/test_mapper.py -v

# 生成覆盖率报告
pytest tests/ --cov=aegis --cov-report=html
```

### 4. 代码质量检查

```bash
# 格式化
black aegis/ tests/
isort aegis/ tests/

# Linting
ruff check aegis/

# 类型检查
mypy aegis/
```

---

## 📝 提交 Pull Request

### 1. 创建分支

```bash
git checkout -b feature/rust-support
```

### 2. 提交更改

```bash
git add .
git commit -m "feat: add Rust language support"
```

**提交消息格式**：

```
<type>: <description>

[optional body]

[optional footer]
```

**Types**：

- `feat`: 新功能
- `fix`: Bug 修复
- `docs`: 文档更新
- `test`: 测试添加/修改
- `refactor`: 代码重构
- `perf`: 性能优化
- `chore`: 构建/工具更改

### 3. 推送并创建 PR

```bash
git push origin feature/rust-support
```

然后在 GitHub 上创建 Pull Request。

---

## ✅ PR 检查清单

提交 PR 前，请确保：

- [ ] 代码通过所有测试（`pytest tests/ -v`）
- [ ] 代码格式化（`black` + `isort`）
- [ ] 代码通过 linting（`ruff check`）
- [ ] 代码通过类型检查（`mypy`）
- [ ] 添加了测试用例
- [ ] 更新了文档（如果需要）
- [ ] 提交消息符合规范
- [ ] PR 描述清晰

---

## 🎨 代码风格

### Python

```python
# ✅ 好的风格
def extract_ast_features(
    file_path: Path,
    language: str
) -> Dict[str, Any]:
    """
    提取 AST 特征

    Args:
        file_path: 文件路径
        language: 编程语言

    Returns:
        提取的特征字典
    """
    features = {}
    # 实现逻辑
    return features

# ❌ 不好的风格
def extract(f, l):  # 名称不清晰
    x = {}  # 变量名无意义
    # 没有文档字符串
    return x
```

### 命名规范

- **函数/变量**: `snake_case`
- **类**: `PascalCase`
- **常量**: `UPPER_SNAKE_CASE`
- **私有方法**: `_leading_underscore`

---

## 📚 文档

### 添加文档字符串

```python
def new_feature(param1: str, param2: int) -> bool:
    """
    功能简短描述

    详细描述（可选）

    Args:
        param1: 参数 1 说明
        param2: 参数 2 说明

    Returns:
        返回值说明

    Raises:
        ValueError: 什么情况下抛出

    Example:
        >>> new_feature("test", 42)
        True
    """
    pass
```

---

## 🐛 报告 Bug

**使用 GitHub Issues**：https://github.com/nexo/aegis-box/issues

**Bug 报告应包含**：

1. **环境信息**
   - 操作系统
   - Python 版本
   - Aegis Box 版本

2. **重现步骤**
   - 详细的步骤
   - 最小化的复现代码

3. **预期行为**
   - 你期望发生什么

4. **实际行为**
   - 实际发生了什么
   - 错误信息/日志

5. **额外信息**
   - 截图
   - 配置文件

---

## 💡 功能请求

**使用 GitHub Issues**：https://github.com/nexo/aegis-box/issues

**功能请求应包含**：

1. **问题描述**
   - 当前的痛点

2. **建议的解决方案**
   - 你希望的功能

3. **替代方案**
   - 其他可能的解决方案

4. **使用场景**
   - 谁会用这个功能
   - 多频繁使用

---

## 🏆 贡献者

感谢所有贡献者！

<!-- 自动生成的贡献者列表 -->
<a href="https://github.com/nexo/aegis-box/graphs/contributors">
  <img src="https://contrib.rocks/image?repo=nexo/aegis-box" />
</a>

---

## 📄 License

通过贡献，你同意你的贡献将在 MIT License 下授权。

---

## ❓ 需要帮助？

- 📧 Email: nexo@example.com
- 💬 Discussions: https://github.com/nexo/aegis-box/discussions
- 🐛 Issues: https://github.com/nexo/aegis-box/issues

---

**🎉 感谢你的贡献！让 Aegis Box 变得更好！**
