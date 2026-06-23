#!/usr/bin/env python3
"""测试 ZAI SDK 连接"""

import os

try:
    from zai import ZaiClient
    
    print("✅ ZAI SDK 导入成功")
    print(f"📦 已安装版本: zai-sdk 0.2.3")
    
    # 检查 API Key
    api_key = os.getenv("ZHIPU_API_KEY")
    
    if api_key:
        print(f"✅ API Key 已设置: {api_key[:8]}...{api_key[-4:]}")
        
        # 初始化客户端
        client = ZaiClient(api_key=api_key)
        print("✅ ZAI 客户端初始化成功")
        
        # 测试简单调用
        print("\n正在测试连接...")
        response = client.chat.completions.create(
            model="glm-4-air",
            messages=[
                {"role": "user", "content": "请回复：Aegis 连接成功，系统就绪。"}
            ],
            max_tokens=50
        )
        
        print("\n" + "="*80)
        print(f"📝 模型响应: {response.choices[0].message.content}")
        print("="*80)
        print("\n✅ ZAI SDK 测试通过！")
        
    else:
        print("⚠️  未设置 ZHIPU_API_KEY 环境变量")
        print("提示: export ZHIPU_API_KEY='your-api-key'")
        print("\n获取 API Key:")
        print("1. 访问: https://open.bigmodel.cn/")
        print("2. 注册并登录")
        print("3. 在控制台获取 API Key")
        
except ImportError as e:
    print(f"❌ 导入失败: {e}")
except Exception as e:
    print(f"❌ 测试失败: {e}")
    import traceback
    traceback.print_exc()
