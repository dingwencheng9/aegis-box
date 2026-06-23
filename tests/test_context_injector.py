"""
测试 Context Injector 的核心功能
"""

import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch

from aegis.engines.context_injector import (
    ContextInjector,
    CIAuditor,
    inject_ide_context,
    run_ci_audit,
)
from aegis.engines.patcher import Vulnerability, ArchitectureReport


# ==========================================
# Fixtures
# ==========================================
@pytest.fixture
def sample_vulnerability():
    """示例漏洞"""
    return Vulnerability(
        file_path="user_service.py",
        description="SQL injection vulnerability",
        severity="CRITICAL",
        suggestion="Use parameterized queries",
        line_number=10
    )


@pytest.fixture
def sample_report(sample_vulnerability):
    """示例架构报告"""
    return ArchitectureReport(
        critical_vulnerabilities=[sample_vulnerability]
    )


# ==========================================
# ContextInjector 测试
# ==========================================
def test_context_injector_initialization(tmp_path):
    """测试 ContextInjector 初始化"""
    injector = ContextInjector(
        project_root=tmp_path,
        target_format="cursorrules"
    )

    assert injector.project_root == tmp_path
    assert injector.target_format == "cursorrules"
    assert injector.target_file == tmp_path / ".cursorrules"


def test_inject_context_new_file(tmp_path, sample_report):
    """测试注入上下文到新文件"""
    injector = ContextInjector(project_root=tmp_path)

    result = injector.inject_context(sample_report)

    assert result.success is True
    assert result.injected is True
    assert injector.target_file.exists()

    # 验证内容
    content = injector.target_file.read_text()
    assert ContextInjector.AEGIS_MARKER_START in content
    assert ContextInjector.AEGIS_MARKER_END in content
    assert "SQL injection vulnerability" in content


def test_inject_context_append_mode(tmp_path, sample_report):
    """测试智能追加模式"""
    injector = ContextInjector(project_root=tmp_path)

    # 先创建一个已有内容的文件
    injector.target_file.write_text("# Existing Rules\n\nSome rules here.")

    result = injector.inject_context(sample_report)

    assert result.success is True

    # 验证已有内容被保留
    content = injector.target_file.read_text()
    assert "# Existing Rules" in content
    assert "Some rules here." in content
    assert ContextInjector.AEGIS_MARKER_START in content


def test_inject_context_update_mode(tmp_path, sample_report):
    """测试幂等性：更新已有的 Aegis 上下文"""
    injector = ContextInjector(project_root=tmp_path)

    # 第一次注入
    result1 = injector.inject_context(sample_report)
    assert result1.success is True

    content1 = injector.target_file.read_text()

    # 第二次注入（幂等性）
    result2 = injector.inject_context(sample_report)
    assert result2.success is True

    content2 = injector.target_file.read_text()

    # 验证内容被更新而非重复追加
    assert content1.count(ContextInjector.AEGIS_MARKER_START) == 1
    assert content2.count(ContextInjector.AEGIS_MARKER_START) == 1


def test_remove_context(tmp_path, sample_report):
    """测试移除 Aegis 上下文"""
    injector = ContextInjector(project_root=tmp_path)

    # 先注入
    injector.inject_context(sample_report)
    assert injector.target_file.exists()

    # 移除
    result = injector.remove_context()

    assert result.success is True
    # 文件应该被删除（因为只有 Aegis 上下文）
    assert not injector.target_file.exists()


def test_remove_context_preserve_other_content(tmp_path, sample_report):
    """测试移除时保留其他内容"""
    injector = ContextInjector(project_root=tmp_path)

    # 先创建已有内容
    injector.target_file.write_text("# Existing Rules\n\nSome rules here.")

    # 注入
    injector.inject_context(sample_report)

    # 移除
    result = injector.remove_context()

    assert result.success is True
    assert injector.target_file.exists()

    # 验证其他内容被保留
    content = injector.target_file.read_text()
    assert "# Existing Rules" in content
    assert ContextInjector.AEGIS_MARKER_START not in content


def test_generate_context_content(tmp_path, sample_report):
    """测试生成上下文内容"""
    injector = ContextInjector(project_root=tmp_path)

    content = injector._generate_context_content(sample_report)

    # 验证内容包含关键信息
    assert ContextInjector.AEGIS_MARKER_START in content
    assert ContextInjector.AEGIS_MARKER_END in content
    assert "SQL injection vulnerability" in content
    assert "user_service.py" in content
    assert "CRITICAL" in content


def test_format_vulnerabilities(tmp_path, sample_report):
    """测试格式化漏洞列表"""
    injector = ContextInjector(project_root=tmp_path)

    formatted = injector._format_vulnerabilities(sample_report.critical_vulnerabilities)

    assert "SQL injection vulnerability" in formatted
    assert "user_service.py" in formatted
    assert "CRITICAL" in formatted


def test_format_vulnerabilities_empty(tmp_path):
    """测试空漏洞列表"""
    injector = ContextInjector(project_root=tmp_path)

    formatted = injector._format_vulnerabilities([])

    assert "未检测到关键漏洞" in formatted


# ==========================================
# CIAuditor 测试
# ==========================================
def test_ci_auditor_initialization(tmp_path):
    """测试 CIAuditor 初始化"""
    auditor = CIAuditor(project_root=tmp_path)

    assert auditor.project_root == tmp_path


def test_run_ci_audit(tmp_path):
    """测试 CI 审计"""
    auditor = CIAuditor(project_root=tmp_path)

    result = auditor.run_ci_audit()

    assert result["success"] is True
    assert "markdown_report" in result
    assert "vulnerabilities_found" in result
    assert "vulnerabilities_fixed" in result


def test_generate_markdown_report(tmp_path):
    """测试生成 Markdown 报告"""
    auditor = CIAuditor(project_root=tmp_path)

    report = auditor._generate_markdown_report()

    assert "Aegis 安全审计报告" in report
    assert "审计时间" in report
    assert "审计结果" in report


# ==========================================
# 外部调用入口测试
# ==========================================
def test_inject_ide_context(tmp_path, sample_report):
    """测试一站式注入入口"""
    result = inject_ide_context(
        report=sample_report,
        project_root=tmp_path
    )

    assert result.success is True
    assert result.injected is True


def test_run_ci_audit_entry(tmp_path):
    """测试一站式 CI 审计入口"""
    result = run_ci_audit(project_root=tmp_path)

    assert result["success"] is True
    assert "markdown_report" in result


# ==========================================
# 边界情况测试
# ==========================================
def test_inject_context_invalid_marker(tmp_path, sample_report):
    """测试不完整的 Aegis 标记"""
    injector = ContextInjector(project_root=tmp_path)

    # 创建一个只有开始标记的文件
    injector.target_file.write_text(
        f"# Existing\n\n{ContextInjector.AEGIS_MARKER_START}\n\nSome content"
    )

    result = injector.inject_context(sample_report)

    assert result.success is True
    # 应该追加新上下文
    content = injector.target_file.read_text()
    assert content.count(ContextInjector.AEGIS_MARKER_START) >= 1
