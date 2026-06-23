#!/usr/bin/env python3
"""
自动生成 CLI 命令文档

从 Typer CLI 定义中提取所有命令和参数，生成 Markdown 文档
"""

import sys
from pathlib import Path
from io import StringIO
from typing import Dict, List

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from aegis.cli import app


def extract_command_info() -> List[Dict]:
    """提取所有命令信息"""
    commands = []

    # 遍历所有注册的命令
    for command_name, command in app.registered_commands:
        # 获取命令回调函数
        callback = command.callback

        # 获取文档字符串
        docstring = callback.__doc__ or "No description available"
        docstring = docstring.strip()

        # 获取参数
        params = []
        if hasattr(command, 'params'):
            for param in command.params:
                param_info = {
                    'name': param.name,
                    'type': str(param.type) if hasattr(param, 'type') else 'str',
                    'default': param.default if hasattr(param, 'default') else None,
                    'help': param.help if hasattr(param, 'help') else '',
                }

                # 判断是否为选项
                if hasattr(param, 'param_type_name'):
                    param_info['is_option'] = param.param_type_name == 'option'
                else:
                    param_info['is_option'] = False

                # 获取选项标志
                if hasattr(param, 'opts'):
                    param_info['opts'] = param.opts
                else:
                    param_info['opts'] = []

                params.append(param_info)

        commands.append({
            'name': command_name,
            'description': docstring,
            'params': params
        })

    return commands


def generate_markdown(commands: List[Dict]) -> str:
    """生成 Markdown 文档"""
    output = StringIO()

    # 写入标题
    output.write("# Aegis CLI 命令手册\n\n")
    output.write("本文档由 `scripts/generate_cli_docs.py` 自动生成，与代码实时同步。\n\n")
    output.write("---\n\n")

    # 写入目录
    output.write("## 📑 目录\n\n")
    for cmd in commands:
        output.write(f"- [`aegis {cmd['name']}`](#{cmd['name']})\n")
    output.write("\n---\n\n")

    # 写入每个命令的详细信息
    for cmd in commands:
        output.write(f"## `aegis {cmd['name']}`\n\n")
        output.write(f"{cmd['description']}\n\n")

        # 写入用法
        output.write("### 用法\n\n")
        output.write("```bash\n")

        # 构建命令行
        usage = f"aegis {cmd['name']}"

        # 添加参数
        args = [p for p in cmd['params'] if not p['is_option']]
        for arg in args:
            usage += f" [{arg['name']}]"

        # 添加选项
        options = [p for p in cmd['params'] if p['is_option']]
        if options:
            usage += " [OPTIONS]"

        output.write(f"{usage}\n")
        output.write("```\n\n")

        # 写入参数说明
        if args:
            output.write("### 参数\n\n")
            output.write("| 参数 | 类型 | 默认值 | 说明 |\n")
            output.write("|------|------|--------|------|\n")

            for arg in args:
                default = arg['default'] if arg['default'] is not None else "-"
                output.write(f"| `{arg['name']}` | {arg['type']} | {default} | {arg['help']} |\n")

            output.write("\n")

        # 写入选项说明
        if options:
            output.write("### 选项\n\n")
            output.write("| 选项 | 类型 | 默认值 | 说明 |\n")
            output.write("|------|------|--------|------|\n")

            for opt in options:
                opts_str = ", ".join([f"`{o}`" for o in opt['opts']])
                default = opt['default'] if opt['default'] is not None else "-"
                output.write(f"| {opts_str} | {opt['type']} | {default} | {opt['help']} |\n")

            output.write("\n")

        # 写入示例
        output.write("### 示例\n\n")
        output.write("```bash\n")

        # 生成示例命令
        if cmd['name'] == 'init':
            output.write("# 初始化配置\n")
            output.write("aegis init\n\n")
            output.write("# 强制覆盖已有配置\n")
            output.write("aegis init --force\n")

        elif cmd['name'] == 'run':
            output.write("# 交互式运行\n")
            output.write("aegis run\n\n")
            output.write("# 全自动模式\n")
            output.write("aegis run --auto\n\n")
            output.write("# 从检查点恢复\n")
            output.write("aegis run --continue\n")

        elif cmd['name'] == 'audit':
            output.write("# 审计当前目录\n")
            output.write("aegis audit\n\n")
            output.write("# 审计指定目录\n")
            output.write("aegis audit src/\n\n")
            output.write("# CI/CD 模式\n")
            output.write("aegis audit --ci-mode --output report.md\n")

        elif cmd['name'] == 'context-sync':
            output.write("# 同步上下文\n")
            output.write("aegis context-sync\n\n")
            output.write("# 指定格式\n")
            output.write("aegis context-sync --format claude_xml\n\n")
            output.write("# 移除上下文\n")
            output.write("aegis context-sync --remove\n")

        else:
            output.write(f"aegis {cmd['name']}\n")

        output.write("```\n\n")
        output.write("---\n\n")

    # 写入底部信息
    output.write("## 🔄 更新此文档\n\n")
    output.write("```bash\n")
    output.write("python scripts/generate_cli_docs.py\n")
    output.write("```\n\n")
    output.write("---\n\n")
    output.write("**🛡️ Aegis Box - CLI 命令文档**\n")

    return output.getvalue()


def main():
    """主函数"""
    print("🔄 生成 CLI 命令文档...")

    # 提取命令信息
    print("📊 提取命令信息...")
    commands = extract_command_info()
    print(f"✅ 找到 {len(commands)} 个命令")

    # 生成 Markdown
    print("📝 生成 Markdown 文档...")
    markdown = generate_markdown(commands)

    # 写入文件
    output_path = project_root / "docs" / "COMMANDS.md"
    output_path.parent.mkdir(exist_ok=True)
    output_path.write_text(markdown, encoding="utf-8")

    print(f"✅ 文档已生成: {output_path}")
    print(f"📄 文档大小: {len(markdown)} 字符")


if __name__ == "__main__":
    main()
