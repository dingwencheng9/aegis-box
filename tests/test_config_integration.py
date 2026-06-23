#!/usr/bin/env python3
"""
集成测试：验证 ConfigLoader 与现有系统的兼容性

测试目标：
1. ConfigLoader 可以正常加载 .env 和 aegis.yaml
2. ConfigManager 集成 ConfigLoader 后功能正常
3. 环境变量引用正确解析
4. 向后兼容：不使用 .env 时仍然正常工作
"""

import os
import sys
import tempfile
import shutil
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

def test_config_loader_basic():
    """测试 ConfigLoader 基本功能"""
    print("🧪 测试 1: ConfigLoader 基本导入和初始化")

    try:
        from aegis.core.config import ConfigLoader

        with tempfile.TemporaryDirectory() as tmpdir:
            loader = ConfigLoader(Path(tmpdir))
            config = loader.load()

            assert isinstance(config, dict), "配置应该返回字典"
            print("   ✅ ConfigLoader 基本功能正常")
            return True
    except Exception as e:
        print(f"   ❌ 失败: {e}")
        return False

def test_env_var_resolution():
    """测试环境变量解析"""
    print("\n🧪 测试 2: 环境变量引用解析")

    try:
        from aegis.core.config import ConfigLoader

        # 设置测试环境变量
        os.environ["TEST_MODEL"] = "claude-opus-4-8"
        os.environ["TEST_API_KEY"] = "sk-test-key"

        with tempfile.TemporaryDirectory() as tmpdir:
            # 创建带环境变量引用的 aegis.yaml
            config_file = Path(tmpdir) / "aegis.yaml"
            config_file.write_text("""
version: "1.0"
llm:
  tier1_fast:
    provider: anthropic
    model: ${TEST_MODEL}
    api_key_env_var: TEST_API_KEY
""")

            loader = ConfigLoader(Path(tmpdir))
            config = loader.load()

            # 验证环境变量被正确解析
            model = config.get("llm", {}).get("tier1_fast", ).get("model")
            assert model == "claude-opus-4-8", f"模型应该被解析为 claude-opus-4-8，实际: {model}"

            print("   ✅ 环境变量引用解析正常")
            return True
    except Exception as e:
        print(f"   ❌ 失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        # 清理环境变量
        os.environ.pop("TEST_MODEL", None)
        os.environ.pop("TEST_API_KEY", None)

def test_backward_compatibility():
    """测试向后兼容性（不使用环境变量引用）"""
    print("\n🧪 测试 3: 向后兼容性（无环境变量引用）")

    try:
        from aegis.core.config import ConfigLoader

        with tempfile.TemporaryDirectory() as tmpdir:
            # 创建传统格式的 aegis.yaml（无环境变量引用）
            config_file = Path(tmpdir) / "aegis.yaml"
            config_file.write_text("""
version: "1.0"
llm:
  tier1_fast:
    provider: zhipu
    model: glm-4-air
    api_key_env_var: ZHIPU_API_KEY
""")

            loader = ConfigLoader(Path(tmpdir))
            config = loader.load()

            # 验证传统配置正常加载
            model = config.get("llm", {}).get("tier1_fast", ).get("model")
            assert model == "glm-4-air", f"模型应该是 glm-4-air，实际: {model}"

            print("   ✅ 向后兼容性正常")
            return True
    except Exception as e:
        print(f"   ❌ 失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_dotenv_loading():
    """测试 .env 文件加载"""
    print("\n🧪 测试 4: .env 文件加载")

    try:
        from aegis.core.config import ConfigLoader

        with tempfile.TemporaryDirectory() as tmpdir:
            # 创建 .env 文件
            env_file = Path(tmpdir) / ".env"
            env_file.write_text("""
ANTHROPIC_API_KEY=sk-ant-test-key
ANTHROPIC_MODEL_TIER2=claude-3-5-sonnet-20241022
""")

            # 创建引用环境变量的 aegis.yaml
            config_file = Path(tmpdir) / "aegis.yaml"
            config_file.write_text("""
version: "1.0"
llm:
  tier2_reasoning:
    provider: anthropic
    model: ${ANTHROPIC_MODEL_TIER2}
    api_key_env_var: ANTHROPIC_API_KEY
""")

            loader = ConfigLoader(Path(tmpdir))
            config = loader.load()

            # 验证 .env 中的值被正确加载和解析
            model = config.get("llm", {}).get("tier2_reasoning", {}).get("model")
            assert model == "claude-3-5-sonnet-20241022", f"模型应该从 .env 加载，实际: {model}"

            # 验证 API key 在环境变量中
            api_key = os.getenv("ANTHROPIC_API_KEY")
            assert api_key == "sk-ant-test-key", "API key 应该被加载到环境变量"

            print("   ✅ .env 文件加载正常")
            return True
    except Exception as e:
        print(f"   ❌ 失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        # 清理环境变量
        os.environ.pop("ANTHROPIC_API_KEY", None)
        os.environ.pop("ANTHROPIC_MODEL_TIER2", None)

def main():
    """运行所有测试"""
    print("=" * 70)
    print("🛡️  Aegis Box - 配置加载器集成测试")
    print("=" * 70)

    results = []

    # 运行测试
    results.append(test_config_loader_basic())
    results.append(test_env_var_resolution())
    results.append(test_backward_compatibility())
    results.append(test_dotenv_loading())

    # 汇总结果
    print("\n" + "=" * 70)
    print("📊 测试结果汇总")
    print("=" * 70)

    passed = sum(results)
    total = len(results)

    print(f"\n通过: {passed}/{total}")

    if passed == total:
        print("\n✅ 所有测试通过！配置加载器集成成功，零破坏性。")
        return 0
    else:
        print(f"\n❌ {total - passed} 个测试失败。")
        return 1

if __name__ == "__main__":
    sys.exit(main())
