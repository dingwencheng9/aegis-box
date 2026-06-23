# 🌐 自定义 API 端点配置指南

## 📋 概述

Aegis Box 支持使用自定义的 API 端点（代理、转发服务等），特别适用于：

- 使用 API 代理服务
- 企业内网转发
- 自建 API 网关
- 负载均衡服务

---

## 🔧 配置自定义端点

### 你的配置信息

**Anthropic API 代理地址**:

```
https://cdn1.yunyi.yun/claude
```

**认证方式**:

- 使用 `x-api-key` header（与官方 API 兼容）
- 格式：Anthropic Messages (原生)

---

## 📝 配置步骤

### Step 1: 编辑 .env 文件

```bash
# 复制模板
cp .env.example .env

# 编辑配置
nano .env
```

### Step 2: 填入配置

```bash
# Anthropic API 配置
ANTHROPIC_API_KEY=your-actual-api-key-here

# 自定义 API 端点（你的代理地址）
ANTHROPIC_API_URL=https://cdn1.yunyi.yun/claude

# Zhipu AI 配置（可选）
ZHIPU_API_KEY=your-zhipu-api-key-here
```

**重要提示**:

- ✅ URL 不要以斜杠 `/` 结尾
- ✅ 使用 `https://` 协议
- ✅ 确保代理服务支持 Anthropic Messages API 格式

---

## 🧪 测试连接

### 运行测试脚本

```bash
.venv/bin/python test_api_complete.py
```

### 预期输出

```
================================================================================
🛡️  Aegis Box - API 连接测试
================================================================================

[1/3] 验证环境变量...

    ✅ ANTHROPIC_API_KEY: sk-ant-a...xxxx

[2/3] 测试 Anthropic API...

    API 端点: https://cdn1.yunyi.yun/claude/v1/messages
    正在连接 Anthropic API...
    ✅ 连接成功！

    ============================================================================
    📝 Claude 响应: Aegis Anthropic 连接成功。
    ============================================================================
```

---

## 🔍 常见问题

### 问题 1: 404 Not Found

**可能原因**:

- API 端点路径错误
- 代理服务配置问题

**解决方案**:

```bash
# 测试基础 URL
curl https://cdn1.yunyi.yun/claude/v1/messages \
  -H "x-api-key: your-key" \
  -H "anthropic-version: 2023-06-01" \
  -H "content-type: application/json" \
  -d '{"model":"claude-3-5-haiku-20241022","max_tokens":10,"messages":[{"role":"user","content":"hi"}]}'
```

### 问题 2: 401 Unauthorized

**可能原因**:

- API Key 无效
- 认证头格式错误

**解决方案**:

1. 确认 API Key 正确
2. 确认代理服务支持 `x-api-key` 认证方式

### 问题 3: 连接超时

**可能原因**:

- 网络连接问题
- 代理服务不可达

**解决方案**:

```bash
# 测试网络连通性
curl -I https://cdn1.yunyi.yun/claude

# 检查 DNS 解析
nslookup cdn1.yunyi.yun
```

### 问题 4: SSL 证书错误

**可能原因**:

- 自签名证书
- 证书过期

**解决方案**:

```bash
# 临时禁用 SSL 验证（仅用于测试）
curl -k https://cdn1.yunyi.yun/claude
```

---

## 🛡️ 安全建议

### 使用代理服务的注意事项

1. **验证代理服务的可信度**
   - ✅ 确认服务提供商的信誉
   - ✅ 检查隐私政策
   - ✅ 确认数据加密

2. **API Key 安全**
   - ✅ 代理服务可能记录你的 API Key
   - ✅ 定期轮换 API Key
   - ✅ 监控 API 使用量

3. **数据隐私**
   - ✅ 代理服务可能记录请求内容
   - ✅ 敏感数据建议使用官方端点
   - ✅ 检查代理服务的日志政策

---

## 📊 端点对比

| 端点类型     | 地址                            | 优势           | 劣势         |
| ------------ | ------------------------------- | -------------- | ------------ |
| **官方端点** | `https://api.anthropic.com`     | 最稳定、最安全 | 可能需要代理 |
| **代理端点** | `https://cdn1.yunyi.yun/claude` | 国内访问快     | 第三方服务   |

---

## 🔄 切换端点

### 切换到官方端点

```bash
# 编辑 .env
nano .env

# 注释掉或删除自定义端点
# ANTHROPIC_API_URL=https://cdn1.yunyi.yun/claude

# 或改为官方端点
ANTHROPIC_API_URL=https://api.anthropic.com
```

### 切换到代理端点

```bash
# 编辑 .env
nano .env

# 设置代理端点
ANTHROPIC_API_URL=https://cdn1.yunyi.yun/claude
```

---

## 🧪 手动测试

### 使用 curl 测试

```bash
# 设置变量
export API_KEY="your-api-key"
export API_URL="https://cdn1.yunyi.yun/claude"

# 发送测试请求
curl "${API_URL}/v1/messages" \
  -H "x-api-key: ${API_KEY}" \
  -H "anthropic-version: 2023-06-01" \
  -H "content-type: application/json" \
  -d '{
    "model": "claude-3-5-haiku-20241022",
    "max_tokens": 100,
    "messages": [
      {
        "role": "user",
        "content": "请回复：Aegis 连接成功。"
      }
    ]
  }'
```

### 预期响应

```json
{
  "id": "msg_xxx",
  "type": "message",
  "role": "assistant",
  "content": [
    {
      "type": "text",
      "text": "Aegis 连接成功。"
    }
  ],
  "model": "claude-3-5-haiku-20241022",
  "stop_reason": "end_turn"
}
```

---

## 📝 配置示例

### 完整 .env 配置

```bash
# ==========================================
# Anthropic API Configuration (代理服务)
# ==========================================
ANTHROPIC_API_KEY=sk-ant-api03-xxxxxxxxxxxxx
ANTHROPIC_API_URL=https://cdn1.yunyi.yun/claude

# ==========================================
# Zhipu AI Configuration
# ==========================================
ZHIPU_API_KEY=xxxxxxxxxxxxxxxxxxxxxxxx

# ==========================================
# OpenAI Configuration (可选)
# ==========================================
# OPENAI_API_KEY=sk-xxxxxxxxxxxxx
```

---

## 🎯 Aegis Box 集成

### 自动识别端点

Aegis Box 会自动：

1. 检查 `ANTHROPIC_API_URL` 环境变量
2. 如果设置，使用自定义端点
3. 如果未设置，使用官方端点 `https://api.anthropic.com`

### 无需修改代码

```python
# Aegis Box 内部实现
api_url = os.getenv("ANTHROPIC_API_URL", "https://api.anthropic.com")
url = f"{api_url.rstrip('/')}/v1/messages"
```

---

## ✅ 验证清单

配置完成后，确认以下内容：

- [ ] `.env` 文件已创建
- [ ] `ANTHROPIC_API_KEY` 已填入
- [ ] `ANTHROPIC_API_URL` 设置为 `https://cdn1.yunyi.yun/claude`
- [ ] URL 没有以斜杠结尾
- [ ] 运行 `test_api_complete.py` 测试通过
- [ ] 看到 "✅ 连接成功" 消息

---

## 📚 相关文档

- **API Key 配置指南**: [API_KEY_SETUP.md](API_KEY_SETUP.md)
- **连接测试报告**: [TEST_CONNECTION_REPORT.md](TEST_CONNECTION_REPORT.md)
- **环境变量模板**: [.env.example](../.env.example)

---

**🌐 自定义端点配置完成！现在可以运行测试验证连接！**
