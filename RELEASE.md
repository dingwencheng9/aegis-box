# 📋 Aegis Box - 发布检查清单 (Release Checklist)

本文档列出了发布到 PyPI 前必须完成的所有检查项。

---

## 🎯 发布前检查

### 1. 版本管理

- [ ] **更新版本号**
  - 文件：`pyproject.toml`
  - 当前版本：`0.1.0`
  - 新版本：`___.___.___`
  - 版本号规范：遵循 [SemVer](https://semver.org/)
    - `MAJOR.MINOR.PATCH`
    - `MAJOR`：不兼容的 API 更改
    - `MINOR`：向后兼容的功能新增
    - `PATCH`：向后兼容的问题修复

- [ ] **更新 `aegis/__init__.py` 中的版本号**

  ```python
  __version__ = "0.1.0"  # 与 pyproject.toml 保持一致
  ```

- [ ] **更新 CHANGELOG.md**
  - 添加新版本的更改日志
  - 包含新增功能、Bug 修复、破坏性更改

---

### 2. 代码质量

- [ ] **所有测试通过**

  ```bash
  # 运行所有测试
  pytest tests/ -v

  # 运行集成测试
  pytest tests/integration/ -v

  # 检查测试覆盖率
  pytest tests/ --cov=aegis --cov-report=html
  ```

- [ ] **代码格式化**

  ```bash
  # Black 格式化
  black aegis/ tests/

  # isort 排序导入
  isort aegis/ tests/
  ```

- [ ] **类型检查**

  ```bash
  # mypy 类型检查
  mypy aegis/
  ```

- [ ] **Linting**

  ```bash
  # ruff 检查
  ruff check aegis/

  # pylint 检查
  pylint aegis/
  ```

---

### 3. 日志质量

- [ ] **所有 CRITICAL 错误有清晰的日志**
  - 搜索所有 `logger.critical()` 调用
  - 确保错误消息清晰、可操作
  - 包含足够的上下文信息

- [ ] **错误处理完善**

  ```python
  # 好的错误日志示例
  try:
      result = dangerous_operation()
  except Exception as e:
      logger.error(
          f"Operation failed: {operation_name}",
          exc_info=True,
          extra={
              "operation": operation_name,
              "input": input_data,
              "error_type": type(e).__name__
          }
      )
  ```

- [ ] **日志级别正确**
  - `DEBUG`：详细的调试信息
  - `INFO`：一般信息（默认显示）
  - `WARNING`：警告信息（不影响运行）
  - `ERROR`：错误信息（功能受影响）
  - `CRITICAL`：严重错误（程序可能崩溃）

---

### 4. 配置与初始化

- [ ] **`aegis init` 在空环境下可用**

  ```bash
  # 测试步骤
  mkdir /tmp/test-aegis
  cd /tmp/test-aegis
  aegis init

  # 验证
  ls -la  # 应该看到 aegis.yaml
  cat aegis.yaml  # 验证配置文件内容
  ```

- [ ] **默认配置合理**
  - API Key 环境变量名称正确
  - 模型名称有效
  - 速率限制合理
  - 忽略规则完整

- [ ] **配置文件迁移**
  - 旧版本配置能正常迁移
  - `aegis config migrate` 命令可用

---

### 5. 依赖管理

- [ ] **依赖版本固定**
  - 检查 `pyproject.toml` 中的依赖版本
  - 确保核心依赖有版本范围限制
  - 避免使用 `*` 或过于宽松的版本范围

- [ ] **依赖安全检查**

  ```bash
  # 使用 safety 检查已知漏洞
  safety check

  # 或使用 pip-audit
  pip-audit
  ```

- [ ] **最小化依赖**
  - 移除未使用的依赖
  - 合并功能相似的依赖

---

### 6. 文档完整性

- [ ] **README.md 完整**
  - 安装说明清晰
  - 快速开始指南有效
  - 架构图准确
  - 示例代码可运行

- [ ] **CLI 命令文档同步**

  ```bash
  # 重新生成命令文档
  python scripts/generate_cli_docs.py

  # 验证
  cat docs/COMMANDS.md
  ```

- [ ] **API 文档生成**

  ```bash
  # 如果有 API 文档，重新生成
  sphinx-build -b html docs/ docs/_build/
  ```

- [ ] **CHANGELOG.md 更新**
  - 添加新版本条目
  - 列出所有重要更改
  - 标注破坏性更改

---

### 7. 打包测试

- [ ] **本地构建测试**

  ```bash
  # 清理旧的构建
  rm -rf dist/ build/ *.egg-info

  # 构建 wheel 和 sdist
  python -m build

  # 验证包内容
  tar -tzf dist/aegis-box-0.1.0.tar.gz
  unzip -l dist/aegis_box-0.1.0-py3-none-any.whl
  ```

- [ ] **本地安装测试**

  ```bash
  # 创建虚拟环境
  python -m venv /tmp/test-venv
  source /tmp/test-venv/bin/activate

  # 从本地 wheel 安装
  pip install dist/aegis_box-0.1.0-py3-none-any.whl

  # 验证安装
  aegis --version
  aegis init

  # 清理
  deactivate
  rm -rf /tmp/test-venv
  ```

- [ ] **TestPyPI 上传测试**

  ```bash
  # 上传到 TestPyPI
  twine upload --repository testpypi dist/*

  # 从 TestPyPI 安装测试
  pip install --index-url https://test.pypi.org/simple/ aegis-box
  ```

---

### 8. 安全检查

- [ ] **敏感信息清理**
  - 搜索代码中的 API Keys
  - 搜索代码中的密码
  - 搜索代码中的 tokens
  - 确认 `.gitignore` 包含敏感文件

- [ ] **示例配置安全**
  - 示例配置中的 API Keys 使用占位符
  - 文档中的示例不包含真实凭据

- [ ] **代码扫描**

  ```bash
  # 使用 bandit 扫描安全问题
  bandit -r aegis/

  # 使用 semgrep 扫描
  semgrep --config=auto aegis/
  ```

---

### 9. License 与版权

- [ ] **LICENSE 文件存在**
  - 确认 LICENSE 文件在项目根目录
  - 内容完整、日期正确

- [ ] **版权声明**
  - 关键文件包含版权声明
  - `pyproject.toml` 中的 license 字段正确

- [ ] **第三方 License 合规**
  - 检查所有依赖的 License
  - 确保与项目 License 兼容

---

### 10. Git 标签与发布

- [ ] **创建 Git 标签**

  ```bash
  # 创建标签
  git tag -a v0.1.0 -m "Release version 0.1.0"

  # 推送标签
  git push origin v0.1.0
  ```

- [ ] **创建 GitHub Release**
  - 标题：`v0.1.0 - [Release Name]`
  - 描述：从 CHANGELOG.md 复制更改日志
  - 附件：上传 wheel 和 sdist

---

## 🚀 发布流程

### 1. 准备阶段

```bash
# 1. 拉取最新代码
git checkout main
git pull origin main

# 2. 更新版本号
# 编辑 pyproject.toml 和 aegis/__init__.py

# 3. 更新 CHANGELOG.md
# 添加新版本的更改日志

# 4. 提交版本更新
git add .
git commit -m "chore: bump version to 0.1.0"
git push origin main
```

---

### 2. 测试阶段

```bash
# 1. 运行所有测试
pytest tests/ -v

# 2. 运行集成测试
pytest tests/integration/ -v

# 3. 代码质量检查
black aegis/ tests/
isort aegis/ tests/
ruff check aegis/
mypy aegis/
```

---

### 3. 构建阶段

```bash
# 1. 清理旧的构建
rm -rf dist/ build/ *.egg-info

# 2. 构建包
python -m build

# 3. 验证包
twine check dist/*
```

---

### 4. 测试发布

```bash
# 1. 上传到 TestPyPI
twine upload --repository testpypi dist/*

# 2. 从 TestPyPI 安装测试
pip install --index-url https://test.pypi.org/simple/ aegis-box

# 3. 验证安装
aegis --version
aegis init
```

---

### 5. 正式发布

```bash
# 1. 上传到 PyPI
twine upload dist/*

# 2. 创建 Git 标签
git tag -a v0.1.0 -m "Release version 0.1.0"
git push origin v0.1.0

# 3. 创建 GitHub Release
# 在 GitHub 上手动创建 Release
```

---

## 📊 发布后验证

- [ ] **PyPI 页面检查**
  - 访问 https://pypi.org/project/aegis-box/
  - 验证版本号正确
  - 验证 README 显示正常
  - 验证下载链接有效

- [ ] **安装验证**

  ```bash
  # 创建新环境
  python -m venv /tmp/verify-venv
  source /tmp/verify-venv/bin/activate

  # 从 PyPI 安装
  pip install aegis-box

  # 验证版本
  aegis --version

  # 运行基本命令
  aegis init

  # 清理
  deactivate
  rm -rf /tmp/verify-venv
  ```

- [ ] **文档链接验证**
  - README 中的链接可访问
  - 文档站点正常
  - 示例代码可运行

---

## 🐛 发布失败恢复

如果发布过程中出现问题：

### 撤回发布（不推荐）

PyPI 不支持删除已发布的版本，但可以：

1. **Yanked Release**
   - 在 PyPI 上标记版本为 "yanked"
   - 用户不会自动安装，但可以显式指定版本安装

2. **发布修复版本**
   - 快速修复问题
   - 发布新的 patch 版本（如 0.1.1）
   - 在 README 中标注问题版本

### 回滚 Git

```bash
# 删除本地标签
git tag -d v0.1.0

# 删除远程标签
git push origin :refs/tags/v0.1.0

# 回滚提交（如果需要）
git revert <commit-hash>
git push origin main
```

---

## 📝 版本号规范

遵循 [Semantic Versioning 2.0.0](https://semver.org/)：

```
MAJOR.MINOR.PATCH

MAJOR: 不兼容的 API 更改
MINOR: 向后兼容的功能新增
PATCH: 向后兼容的问题修复
```

### 版本号示例

- `0.1.0` → `0.1.1`：Bug 修复
- `0.1.0` → `0.2.0`：新增功能
- `0.1.0` → `1.0.0`：第一个稳定版本
- `1.0.0` → `2.0.0`：破坏性更改

### Pre-release 版本

- `0.1.0-alpha.1`：Alpha 版本
- `0.1.0-beta.1`：Beta 版本
- `0.1.0-rc.1`：Release Candidate

---

## 🎉 发布完成

发布完成后：

1. **更新文档**
   - 更新 README 中的版本徽章
   - 更新文档站点

2. **通知用户**
   - 在 GitHub 发布公告
   - 在社交媒体分享
   - 在相关社区宣传

3. **监控反馈**
   - 关注 GitHub Issues
   - 关注 PyPI 下载量
   - 收集用户反馈

---

**🛡️ Aegis Box - 发布检查清单**

**当前版本**: 0.1.0  
**下一版本**: **_._**.**\_  
**发布日期**: \*\***\_**\*\***
