# 🔑 API Key 配置与测试指南

## 📋 配置步骤

### Step 1: 复制配置模板

```bash
cp .env.example .env
```

---

### Step 2: 获取 API Keys

#### Anthropic API Key (Claude)

1. **访问**: https://console.anthropic.com/
2. **注册/登录** Anthropic 账户
3. **导航**: Settings → API Keys
4. **创建**: Create Key
5. **复制**: API Key (格式: `sk-ant-api03-...`)

**用途**: Claude 3.5 Haiku / Sonnet (Tier 2/3 模型)

---

#### Zhipu AI API Key (GLM)

1. **访问**: https://open.bigmodel.cn/
2. **注册/登录** 智谱 AI 账户
3. **导航**: 控制台 → API Keys
4. **创建**: 生成新的 API Key
5. **复制**: API Key

**用途**: GLM-4-Air / GLM-4 (Tier 1 模型)

---

### Step 3: 编辑 .env 文件

```bash
# 使用你喜欢的编辑器打开
nano .env
# 或
vim .env
# 或
code .env
```

将 `.env` 文件中的占位符替换为真实的 API Key：

```bash
# 原内容
ANTHROPIC_API_KEY=your-anthropic-api-key-here
ZHIPU_API_KEY=your-zhipu-api-key-here

# 修改为
ANTHROPIC_API_KEY=sk-ant-api03-xxxxxxxxxxxxx
ZHIPU_API_KEY=xxxxxxxxxxxxxxxxxxxxxxxx
```

**注意**:

- ✅ 不要包含引号
- ✅ 不要有额外的空格
- ✅ 每个 Key 独立一行

---

### Step 4: 运行测试

```bash
.venv/bin/python test_api_complete.py
```

---

## 📊 预期输出

### 成功情况

```
================================================================================
🛡️  Aegis Box - API 连接测试
================================================================================

[1/3] 验证环境变量...

    ✅ ANTHROPIC_API_KEY: sk-ant-a...xxxx
    ✅ ZHIPU_API_KEY: xxxxxxxx...xxxx

[2/3] 测试 Anthropic API...

    正在连接 Anthropic API...
    ✅ 连接成功！

    ============================================================================
    📝 Claude 响应: Aegis Anthropic 连接成功。
    ============================================================================

[3/3] 测试 Zhipu AI API...

    正在初始化 ZAI 客户端...
    正在连接 Zhipu AI API...
    ✅ 连接成功！

    ============================================================================
    📝 GLM 响应: Aegis Zhipu 连接成功。
    ============================================================================

================================================================================
📊 测试总结
================================================================================

✅ Anthropic API (Claude) - 已配置并测试
✅ Zhipu AI API (GLM) - 已配置并测试

🎉 至少有一个 API 配置成功！Aegis Box 可以正常工作。

================================================================================
```

---

## 🔧 故障排查

### 问题 1: API Key 未找到

**错误信息**:

```
⚠️  ANTHROPIC_API_KEY: 未设置
```

**解决方案**:

1. 确认 `.env` 文件存在
2. 确认 API Key 已正确填入
3. 确认没有多余的引号或空格
4. 重新运行测试脚本

---

### 问题 2: Anthropic API 401 错误

**错误信息**:

```
❌ HTTP 错误: 401
响应: {"type":"error","error":{"type":"authentication_error",...}}
```

**原因**: API Key 无效或已过期

**解决方案**:

1. 访问 https://console.anthropic.com/
2. 检查 API Key 是否有效
3. 检查账户余额是否充足
4. 重新生成 API Key

---

### 问题 3: Zhipu AI API 错误

**错误信息**:

```
❌ 错误: ...
```

**解决方案**:

1. 访问 https://open.bigmodel.cn/
2. 检查 API Key 是否有效
3. 检查账户余额是否充足
4. 确认已安装 zai-sdk: `uv pip install zai-sdk`

---

### 问题 4: 连接超时

**错误信息**:

```
❌ 连接超时
```

**原因**: 网络连接问题

**解决方案**:

1. 检查网络连接
2. 检查是否需要代理
3. 尝试更换网络环境
4. 增加超时时间

---

## 🔐 安全建议

### ✅ 推荐做法

1. **使用 .env 文件** (不要硬编码)

   ```python
   # ✅ 好
   api_key = os.getenv("ANTHROPIC_API_KEY")

   # ❌ 坏
   api_key = "sk-ant-api03-xxxxx"
   ```

2. **添加到 .gitignore**

   ```bash
   echo ".env" >> .gitignore
   ```

3. **不要提交到 Git**

   ```bash
   # 检查 .env 是否被忽略
   git status
   # 应该看不到 .env 文件
   ```

4. **定期轮换 API Keys**
   - 每 3-6 个月更换一次
   - 发现泄露立即更换

---

### ❌ 避免的做法

1. ❌ 不要硬编码 API Key 到代码中
2. ❌ 不要将 `.env` 文件提交到 Git
3. ❌ 不要在公开场合分享 API Key
4. ❌ 不要使用弱密码保护 API Key
5. ❌ 不要将 API Key 写入日志文件

---

## 📝 环境变量说明

### ANTHROPIC_API_KEY

- **格式**: `sk-ant-api03-...`
- **长度**: 约 108 字符
- **用途**: Claude 3.5 Haiku, Claude 3.5 Sonnet
- **成本**: $0.80/1M input tokens (Haiku)
- **获取**: https://console.anthropic.com/

### ZHIPU_API_KEY

- **格式**: 字母数字组合
- **长度**: 约 32-64 字符
- **用途**: GLM-4-Air, GLM-4, GLM-4-Plus
- **成本**: ¥0.001/1k tokens (GLM-4-Air)
- **获取**: https://open.bigmodel.cn/

### OPENAI_API_KEY (可选)

- **格式**: `sk-...`
- **长度**: 约 51 字符
- **用途**: GPT-4, GPT-4o-mini
- **成本**: $0.15/1M input tokens (GPT-4o-mini)
- **获取**: https://platform.openai.com/

---

## 🚀 下一步

### 配置完成后

1. **测试 Aegis Box**:

   ```bash
   .venv/bin/python -m aegis.cli init
   ```

2. **运行完整测试**:

   ```bash
   .venv/bin/python test_connection.py
   ```

3. **查看配置**:
   ```bash
   cat aegis.yaml
   ```

---

## 📚 相关文档

- **Anthropic API 文档**: https://docs.anthropic.com/
- **Zhipu AI 文档**: https://open.bigmodel.cn/dev/api
- **Aegis Box README**: [README.md](../README.md)
- **连接测试报告**: [TEST_CONNECTION_REPORT.md](TEST_CONNECTION_REPORT.md)

---

## 💡 推荐配置

### 个人开发（成本优先）

```bash
# 只配置智谱 AI (最便宜)
ZHIPU_API_KEY=your-key
```

### 生产环境（质量优先）

```bash
# 配置 Anthropic (最高质量)
ANTHROPIC_API_KEY=your-key
```

### 完整配置（最佳体验）

```bash
# 配置两者 (速度 + 质量)
ANTHROPIC_API_KEY=your-key
ZHIPU_API_KEY=your-key
```

**Aegis Box 推荐配置**:

- Tier 1 (快速探伤): GLM-4-Air
- Tier 2 (架构推理): Claude-3.5-Haiku
- Tier 3 (补丁生成): Claude-3.5-Sonnet

---

**🔑 配置完成后，运行测试验证连接！**
