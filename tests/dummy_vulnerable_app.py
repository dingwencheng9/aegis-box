"""
🔴 危险示例代码 - 包含多个明显的安全漏洞
仅用于测试 Aegis 的漏洞检测和自动修复能力
"""

import os
import sqlite3


def execute_user_command(user_input: str):
    """
    🔴 命令注入漏洞 (Command Injection)
    危险：直接将用户输入拼接到 shell 命令中
    """
    # 极其危险的代码！
    command = f"echo {user_input}"
    os.system(command)  # ❌ 用户可以注入 `; rm -rf /`


def search_user(username: str):
    """
    🔴 SQL 注入漏洞 (SQL Injection)
    危险：直接将用户输入拼接到 SQL 查询中
    """
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()

    # 极其危险的查询！
    query = f"SELECT * FROM users WHERE username = '{username}'"
    cursor.execute(query)  # ❌ 用户可以注入 `' OR '1'='1`

    results = cursor.fetchall()
    conn.close()
    return results


def read_user_file(filename: str):
    """
    🔴 路径遍历漏洞 (Path Traversal)
    危险：未验证文件路径，可能读取系统敏感文件
    """
    # 没有路径验证！
    with open(filename, 'r') as f:  # ❌ 用户可以传入 `../../etc/passwd`
        return f.read()


def render_html(user_content: str):
    """
    🔴 XSS 跨站脚本漏洞 (Cross-Site Scripting)
    危险：未转义用户输入直接插入 HTML
    """
    # 未转义用户输入！
    html = f"<div>{user_content}</div>"  # ❌ 用户可以注入 `<script>alert('xss')</script>`
    return html


# 模拟 API 端点
def api_endpoint(request_data):
    """
    模拟的 API 入口点
    """
    action = request_data.get('action')
    data = request_data.get('data')

    if action == 'command':
        execute_user_command(data)
    elif action == 'search':
        return search_user(data)
    elif action == 'read':
        return read_user_file(data)
    elif action == 'render':
        return render_html(data)
