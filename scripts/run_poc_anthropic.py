#!/usr/bin/env python3
"""
🔥 Aegis PoC - 受控漏洞点火试验（Anthropic Only 版本）
Proof of Concept: 单文件漏洞检测 → LLM 审计 → 自动修复

临时配置：由于智谱 AI 余额不足，全部使用 Anthropic 模型
- Tier-1: Claude Haiku 4.5 (快速审计)
- Tier-2: Claude Sonnet 4.6 (架构分析)
- Tier-3: Claude Opus 4.8 (生成补丁)
"""

import asyncio
import sys
from pathlib import Path
from loguru import logger

# 添加项目根目录到 sys.path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from aegis.cli import AegisConfig, ModelTierConfig
from aegis.engines.mapper import CodeMapper
from aegis.engines.reducer import ArchitectureReducer
from aegis.engines.patcher import SmartPatcher
from aegis.utils.git_sandbox import GitSandbox


async def main():
    """主流程"""
    logger.info("=" * 80)
    logger.info("🔥 Aegis PoC - 受控漏洞点火试验 (Anthropic Only)")
    logger.info("=" * 80)

    # 临时配置：全部使用 Anthropic 模型
    config = AegisConfig()
    config.llm["tier1_fast"] = ModelTierConfig(
        provider="anthropic",
        model="claude-haiku-4-5-20251001",  # 快速且便宜
        api_key_env_var="ANTHROPIC_API_KEY"
    )
    config.llm["tier2_reasoning"] = ModelTierConfig(
        provider="anthropic",
        model="claude-sonnet-4-6",  # 深度推理
        api_key_env_var="ANTHROPIC_API_KEY"
    )
    config.llm["tier3_patching"] = ModelTierConfig(
        provider="anthropic",
        model="claude-opus-4-8",  # 生成补丁
        api_key_env_var="ANTHROPIC_API_KEY"
    )

    target_file = project_root / "tests" / "dummy_vulnerable_app.py"

    if not target_file.exists():
        logger.error(f"❌ 目标文件不存在: {target_file}")
        return

    logger.info(f"🎯 目标文件: {target_file}")
    logger.info(f"📋 模型配置:")
    logger.info(f"   - Tier-1: {config.llm['tier1_fast'].provider}/{config.llm['tier1_fast'].model}")
    logger.info(f"   - Tier-2: {config.llm['tier2_reasoning'].provider}/{config.llm['tier2_reasoning'].model}")
    logger.info(f"   - Tier-3: {config.llm['tier3_patching'].provider}/{config.llm['tier3_patching'].model}")
    logger.info("")

    # ========================================
    # Step 1: 提取代码骨架
    # ========================================
    logger.info("Step 1: 📄 提取代码骨架 (AST)")
    logger.info("-" * 80)

    mapper = CodeMapper()
    skeleton = mapper.extract_skeleton(target_file)

    if not skeleton:
        logger.error("❌ 骨架提取失败")
        return

    logger.success(f"✅ 骨架提取成功")
    logger.info(f"   - 总行数: {skeleton.total_lines}")
    logger.info(f"   - 骨架行数: {skeleton.skeleton_lines}")
    logger.info(f"   - 压缩率: {skeleton.compression_ratio:.1%}")
    logger.info(f"   - 函数数量: {len(skeleton.functions)}")
    logger.info("")

    # ========================================
    # Step 2: Tier-1 审计文件
    # ========================================
    logger.info("Step 2: 🔍 Tier-1 审计 (Claude Haiku 4.5)")
    logger.info("-" * 80)

    reducer = ArchitectureReducer(config=config)

    try:
        file_summary = await reducer.analyze_file(skeleton)

        logger.success("✅ Tier-1 审计完成")
        logger.info(f"   - 状态: {file_summary.status}")
        logger.info(f"   - 职责: {file_summary.responsibility}")
        logger.info(f"   - 暴露接口: {len(file_summary.exposed_interfaces)} 个")
        logger.info(f"   - 发现漏洞: {len(file_summary.vulnerabilities)} 个")

        if file_summary.vulnerabilities:
            logger.warning("")
            logger.warning("🚨 发现的漏洞:")
            for i, vuln in enumerate(file_summary.vulnerabilities, 1):
                logger.warning(f"   {i}. [{vuln.level}] {vuln.description}")
                if vuln.location:
                    logger.warning(f"      位置: {vuln.location}")
                if vuln.suggestion:
                    logger.warning(f"      建议: {vuln.suggestion}")

        logger.info("")

    except Exception as e:
        logger.error(f"❌ Tier-1 审计失败: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return

    # ========================================
    # Step 3: Tier-2 架构分析
    # ========================================
    logger.info("Step 3: 🏛️ Tier-2 架构分析 (Claude Sonnet 4.6)")
    logger.info("-" * 80)

    try:
        # 调用完整分析（会触发 Tier-2）
        report = await reducer.analyze_project([skeleton])

        logger.success("✅ Tier-2 架构分析完成")
        logger.info(f"   - 分析文件数: {report.analyzed_files}")
        logger.info(f"   - 架构评价: {report.architecture_overview[:100]}...")
        logger.info(f"   - 关键漏洞: {len(report.critical_vulnerabilities)} 个")
        logger.info(f"   - 重构建议: {len(report.top_refactoring_actions)} 个")
        logger.info("")

        if report.critical_vulnerabilities:
            logger.warning("🚨 关键漏洞清单:")
            for i, vuln in enumerate(report.critical_vulnerabilities, 1):
                logger.warning(f"   {i}. {vuln}")

        logger.info("")

    except Exception as e:
        logger.error(f"❌ Tier-2 分析失败: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return

    # ========================================
    # Step 4: Tier-3 生成补丁
    # ========================================
    logger.info("Step 4: 🛠️ Tier-3 生成修复补丁 (Claude Opus 4.8)")
    logger.info("-" * 80)

    # 只处理 P0 漏洞
    p0_vulns = [v for v in file_summary.vulnerabilities if v.level == "P0"]

    if not p0_vulns:
        logger.warning("⚠️ 未发现 P0 级别漏洞，跳过补丁生成")
        logger.info("")
        logger.success("🎉 PoC 测试完成！")
        return

    logger.info(f"🎯 准备修复 {len(p0_vulns)} 个 P0 漏洞")

    try:
        # 初始化 Git 沙盒
        sandbox = GitSandbox(project_root)
        sandbox.create_sandbox_branch("aegis-poc-fix")

        # 初始化 Patcher
        patcher = SmartPatcher(repo_path=project_root, config=config)

        # 逐个生成补丁
        for i, vuln in enumerate(p0_vulns, 1):
            logger.info(f"")
            logger.info(f"修复漏洞 {i}/{len(p0_vulns)}: {vuln.description}")

            # 构建漏洞信息
            from aegis.engines.reducer import VulnerabilityItem as VulnItem
            vuln_obj = VulnItem(
                level=vuln.level,
                description=vuln.description,
                location=vuln.location,
                suggestion=vuln.suggestion
            )

            # 调用 Tier-3 生成补丁
            result = await patcher.heal_single_vulnerability(
                file_path=target_file,
                vulnerability=vuln_obj,
                code_skeleton=skeleton
            )

            if result.success:
                logger.success(f"✅ 补丁生成成功")
                logger.info(f"   - 修改: {result.diff_summary}")
            else:
                logger.error(f"❌ 补丁生成失败: {result.error_message}")

        logger.info("")
        logger.success("🎉 PoC 测试完成！")

    except Exception as e:
        logger.error(f"❌ 补丁生成失败: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return


if __name__ == "__main__":
    # 配置日志格式
    logger.remove()
    logger.add(
        sys.stderr,
        format="<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <level>{message}</level>",
        level="DEBUG"
    )

    asyncio.run(main())
