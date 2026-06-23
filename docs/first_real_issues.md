# 🐛 首批真实 Issue（基于开发过程中的实际痛点）

这些 Issue 反映了 Aegis Box 开发过程中遇到的真实技术挑战和未完美解决的边界情况。它们需要社区的智慧来完善。

---

## Issue #1: 🔧 [Bug] AST 解析在复杂嵌套结构中的性能退化

### 🏷️ 标签

`bug`, `performance`, `help-wanted`, `ast-parsing`

### 📝 问题描述

在开发 `aegis/engines/mapper.py` 的 AST 提取引擎时，我们发现当处理深度嵌套的代码结构（如 10+ 层的类嵌套或递归函数定义）时，tree-sitter 的遍历性能会显著下降。

**具体表现**：

- 普通文件（< 500 行）：AST 提取 < 100ms
- 复杂嵌套文件（> 1000 行 + 深层嵌套）：AST 提取 > 5s
- 最坏情况：某些生成的代码文件（如 protobuf 生成的 Python 文件）可能超过 30s

### 🔬 复现路径

1. 创建一个深度嵌套的 Python 文件 `test_nested.py`：

```python
class Level1:
    class Level2:
        class Level3:
            class Level4:
                class Level5:
                    class Level6:
                        class Level7:
                            class Level8:
                                class Level9:
                                    class Level10:
                                        def deeply_nested_method(self):
                                            pass
```

2. 使用 Aegis 审计该文件：

```bash
aegis audit test_nested.py
```

3. 观察日志中的 AST 提取耗时

### 🎯 问题根源

在 `aegis/engines/mapper.py` 的 `extract_ast_skeleton()` 方法中，我们采用了递归遍历策略：

```python
def _traverse_node(self, node, depth=0):
    if depth > 100:  # 硬编码的深度限制
        return
    for child in node.children:
        self._traverse_node(child, depth + 1)
```

**问题**：

1. 递归深度限制（100）太过粗暴
2. 没有针对特定节点类型（如类定义）进行优化
3. 对于生成的代码（protobuf, gRPC），应该跳过而非强行解析

### 💡 期望的解决方案

1. **智能深度控制**：
   - 对于类定义，限制嵌套深度为 5 层
   - 对于函数定义，限制为 10 层
   - 添加启发式检测：如果检测到文件名包含 `_pb2.py`（protobuf 生成文件），直接跳过

2. **增量解析**：
   - 当检测到深层嵌套时，切换到"采样模式"
   - 只提取顶层和第 1-2 层的结构，忽略深层细节

3. **性能监控**：
   - 添加 `AEGIS_PROFILE=1` 环境变量
   - 输出每个文件的 AST 提取耗时
   - 记录到 `artifacts/performance.log`

### 🔗 相关代码

- `aegis/engines/mapper.py:150-200` (AST 遍历逻辑)
- `aegis/utils/ast_utils.py` (tree-sitter 配置)

### 📊 影响范围

- **影响用户**：处理大型 codebase（特别是包含 protobuf 或自动生成代码）的用户
- **严重程度**：Medium（不阻塞核心功能，但影响体验）
- **复现频率**：约 10% 的项目会遇到

### 🤝 如何贡献

1. Fork 仓库
2. 在 `tests/test_mapper.py` 中添加性能测试用例
3. 实现智能深度控制逻辑
4. 确保现有测试仍然通过
5. 提交 PR

### 🎯 验收标准

- [ ] 对于 10 层嵌套的文件，AST 提取 < 1s
- [ ] protobuf 生成文件自动跳过
- [ ] 添加性能分析日志
- [ ] 所有现有测试通过
- [ ] 新增至少 3 个针对深层嵌套的测试用例

---

## Issue #2: 🔧 [Enhancement] Git Sandbox 在 Windows 下的路径规范化问题

### 🏷️ 标签

`enhancement`, `windows`, `help-wanted`, `cross-platform`, `good-first-issue`

### 📝 问题描述

在开发 `aegis/utils/git_sandbox.py` 的 Git 沙盒隔离功能时，我们发现 Windows 环境下的路径处理存在不一致性。

**具体表现**：

- macOS/Linux：使用 `/` 作为路径分隔符，一切正常
- Windows：混用 `\` 和 `/`，导致以下问题：
  1. Git 操作失败（Git 期望 `/`）
  2. 文件匹配失败（`glob.glob()` 在 Windows 下行为不同）
  3. 日志输出混乱（路径显示不一致）

### 🔬 复现路径

**环境**：Windows 10/11

1. 克隆 Aegis Box 到 Windows 机器
2. 运行以下命令：

```bash
aegis patch examples\test_project\user_service.py
```

3. 观察错误：

```
ERROR: Failed to create Git branch: Invalid path 'examples\test_project\user_service.py'
Git expected: examples/test_project/user_service.py
```

### 🎯 问题根源

在 `aegis/utils/git_sandbox.py` 中，我们使用了字符串拼接来构建路径：

```python
# ❌ 当前实现（有问题）
def _create_branch(self, file_path: str):
    branch_name = f"aegis-patch-{file_path.replace('/', '-')}"
    # 问题：Windows 下 file_path 可能包含 '\'
```

**问题**：

1. 没有使用 `pathlib.Path` 进行路径规范化
2. 假设路径分隔符总是 `/`
3. 在调用 Git 命令前没有转换为 POSIX 路径

### 💡 期望的解决方案

1. **全面使用 `pathlib.Path`**：

```python
from pathlib import Path

def _create_branch(self, file_path: str):
    # ✅ 新实现
    path = Path(file_path)
    # 转换为 POSIX 路径（Git 总是使用 /）
    posix_path = path.as_posix()
    branch_name = f"aegis-patch-{posix_path.replace('/', '-')}"
```

2. **路径规范化工具函数**：

在 `aegis/utils/path_utils.py` 中添加：

```python
from pathlib import Path
import os

def normalize_path(path: str | Path) -> Path:
    """规范化路径，跨平台兼容"""
    return Path(path).resolve()

def to_posix_path(path: str | Path) -> str:
    """转换为 POSIX 路径（Git 兼容）"""
    return Path(path).as_posix()

def ensure_relative_path(path: str | Path, base: str | Path) -> Path:
    """确保路径是相对路径"""
    path = Path(path).resolve()
    base = Path(base).resolve()
    return path.relative_to(base)
```

3. **重构 Git Sandbox**：

在 `aegis/utils/git_sandbox.py` 中：

- 所有路径操作使用 `pathlib.Path`
- 调用 Git 命令前，使用 `to_posix_path()` 转换
- 文件匹配使用 `Path.glob()` 而非 `glob.glob()`

### 🔗 相关代码

- `aegis/utils/git_sandbox.py` (整个文件需要重构)
- `aegis/engines/patcher.py:50-100` (调用 Git Sandbox 的地方)
- `aegis/engines/sweeper.py:30-80` (文件扫描逻辑)

### 📊 影响范围

- **影响用户**：所有 Windows 用户
- **严重程度**：High（Windows 用户无法使用补丁功能）
- **复现频率**：100%（在 Windows 上）

### 🤝 如何贡献

1. Fork 仓库
2. 创建 `aegis/utils/path_utils.py` 工具文件
3. 重构 `git_sandbox.py` 使用 `pathlib.Path`
4. 在 Windows 环境下测试
5. 添加 Windows CI 测试（`.github/workflows/ci.yml` 已配置）
6. 提交 PR

### 🎯 验收标准

- [ ] 所有路径操作使用 `pathlib.Path`
- [ ] Git 命令使用 POSIX 路径
- [ ] Windows CI 测试通过
- [ ] 添加至少 5 个跨平台路径测试用例
- [ ] 文档更新（说明路径处理逻辑）

### 💡 为什么这是 Good First Issue

1. **范围明确**：只需要重构路径处理逻辑
2. **影响可见**：修复后 Windows 用户立即受益
3. **学习价值**：掌握 Python 跨平台路径处理最佳实践
4. **测试友好**：可以在本地充分测试（不需要复杂环境）

### 📚 参考资料

- [Python pathlib 官方文档](https://docs.python.org/3/library/pathlib.html)
- [Git 路径规范](https://git-scm.com/docs/git-add#_pathnames)
- [跨平台 Python 代码最佳实践](https://docs.python-guide.org/writing/structure/)

---

## 🎯 贡献指南

这两个 Issue 是基于 Aegis Box 实际开发中遇到的真实问题。我们需要社区的帮助来完善这些边界情况。

### 如何认领

1. 在 Issue 下评论 "我想认领这个任务"
2. 维护者会在 24 小时内回复并分配
3. 开始工作前，建议先在 Issue 下讨论技术方案
4. 提交 PR 时，引用 Issue 编号

### 需要帮助？

- 💬 在 Issue 下提问
- 📧 发邮件到 nexo@example.com
- 🐦 Twitter: @aegis_box (即将开通)

---

**🛡️ 感谢你帮助 Aegis Box 变得更好！**
