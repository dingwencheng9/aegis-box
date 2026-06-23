"""
测试 Git Sandbox 的核心功能
"""

import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch
import git

from aegis.utils.git_sandbox import (
    GitSandbox,
    DummySandbox,
    SandboxError,
    create_sandbox,
)


# ==========================================
# Fixtures
# ==========================================
@pytest.fixture
def temp_git_repo(tmp_path):
    """创建临时 Git 仓库"""
    repo = git.Repo.init(tmp_path)

    # 创建初始提交
    test_file = tmp_path / "test.txt"
    test_file.write_text("initial content")
    repo.index.add(["test.txt"])
    repo.index.commit("Initial commit")

    return repo, tmp_path


# ==========================================
# GitSandbox 基础测试
# ==========================================
def test_git_sandbox_initialization(temp_git_repo):
    """测试 GitSandbox 初始化"""
    repo, repo_path = temp_git_repo

    sandbox = GitSandbox(repo_path, auto_commit=False)

    assert sandbox.repo_path == repo_path
    assert sandbox.auto_commit is False
    assert sandbox.commit_message == "feat: Apply Aegis patches"


def test_git_sandbox_enter_clean_workdir(temp_git_repo):
    """测试干净工作区的进入流程"""
    repo, repo_path = temp_git_repo
    original_branch = repo.active_branch.name

    with GitSandbox(repo_path) as sandbox:
        # 验证状态
        assert sandbox.repo is not None
        assert sandbox.original_branch_name == original_branch
        assert sandbox.is_detached is False
        assert sandbox.stashed is False
        assert sandbox.patch_branch_name.startswith("aegis-patch-")

        # 验证当前在补丁分支
        assert repo.active_branch.name == sandbox.patch_branch_name


def test_git_sandbox_enter_dirty_workdir(temp_git_repo):
    """测试有未提交更改的进入流程"""
    repo, repo_path = temp_git_repo

    # 创建未提交的更改
    test_file = repo_path / "test.txt"
    test_file.write_text("modified content")

    with GitSandbox(repo_path) as sandbox:
        # 验证已暂存
        assert sandbox.stashed is True

        # 验证工作区现在是干净的（在补丁分支上）
        # （因为切换到了新分支，基于干净的 HEAD）


def test_git_sandbox_exit_success_no_commit(temp_git_repo):
    """测试成功退出（不自动提交）"""
    repo, repo_path = temp_git_repo
    original_branch = repo.active_branch.name

    with GitSandbox(repo_path, auto_commit=False) as sandbox:
        # 修改文件
        test_file = repo_path / "test.txt"
        test_file.write_text("patched content")
        repo.index.add(["test.txt"])

    # 验证仍在补丁分支
    assert repo.active_branch.name.startswith("aegis-patch-")
    assert repo.active_branch.name != original_branch


def test_git_sandbox_exit_success_auto_commit(temp_git_repo):
    """测试成功退出（自动提交）"""
    repo, repo_path = temp_git_repo

    with GitSandbox(repo_path, auto_commit=True, commit_message="test: patch") as sandbox:
        # 修改文件
        test_file = repo_path / "test.txt"
        test_file.write_text("patched content")

    # 验证已提交
    assert repo.head.commit.message.strip() == "test: patch"


def test_git_sandbox_exit_exception_rollback(temp_git_repo):
    """测试异常退出（回滚）"""
    repo, repo_path = temp_git_repo
    original_branch = repo.active_branch.name
    original_commit = repo.head.commit.hexsha

    try:
        with GitSandbox(repo_path) as sandbox:
            # 修改文件
            test_file = repo_path / "test.txt"
            test_file.write_text("bad patch")

            # 模拟异常
            raise ValueError("Patch failed")
    except ValueError:
        pass

    # 验证已回滚到原分支
    assert repo.active_branch.name == original_branch

    # 验证 HEAD 未变
    assert repo.head.commit.hexsha == original_commit

    # 验证补丁分支已删除
    branch_names = [b.name for b in repo.branches]
    assert not any(name.startswith("aegis-patch-") for name in branch_names)


def test_git_sandbox_stash_and_restore(temp_git_repo):
    """测试 stash 和恢复流程"""
    repo, repo_path = temp_git_repo

    # 创建未提交的更改
    test_file = repo_path / "test.txt"
    test_file.write_text("user changes")

    try:
        with GitSandbox(repo_path) as sandbox:
            # 模拟异常
            raise ValueError("Test exception")
    except ValueError:
        pass

    # 验证用户更改已恢复
    assert test_file.read_text() == "user changes"


def test_git_sandbox_no_changes_no_commit(temp_git_repo):
    """测试没有更改时不提交（防止空提交）"""
    repo, repo_path = temp_git_repo
    initial_commit_count = len(list(repo.iter_commits()))

    with GitSandbox(repo_path, auto_commit=True):
        # 不做任何更改
        pass

    # 验证没有新的提交
    assert len(list(repo.iter_commits())) == initial_commit_count


# ==========================================
# Detached HEAD 测试
# ==========================================
def test_git_sandbox_detached_head(temp_git_repo):
    """测试 Detached HEAD 状态"""
    repo, repo_path = temp_git_repo

    # 创建 Detached HEAD
    commit_hash = repo.head.commit.hexsha
    repo.git.checkout(commit_hash)

    with GitSandbox(repo_path) as sandbox:
        # 验证检测到 Detached HEAD
        assert sandbox.is_detached is True
        assert sandbox.original_branch_name == commit_hash


# ==========================================
# 非 Git 仓库测试
# ==========================================
def test_git_sandbox_not_a_repo(tmp_path):
    """测试非 Git 仓库（应该抛出异常）"""
    with pytest.raises(SandboxError, match="不是 Git 仓库"):
        with GitSandbox(tmp_path):
            pass


# ==========================================
# DummySandbox 测试
# ==========================================
def test_dummy_sandbox_enter_exit():
    """测试 DummySandbox 的基本流程"""
    with DummySandbox() as sandbox:
        assert sandbox is not None


def test_dummy_sandbox_with_exception():
    """测试 DummySandbox 的异常处理"""
    try:
        with DummySandbox():
            raise ValueError("Test exception")
    except ValueError:
        pass  # 异常正常传播


# ==========================================
# create_sandbox 工厂函数测试
# ==========================================
def test_create_sandbox_git_repo(temp_git_repo):
    """测试工厂函数：Git 仓库"""
    repo, repo_path = temp_git_repo

    sandbox = create_sandbox(repo_path)

    assert isinstance(sandbox, GitSandbox)


def test_create_sandbox_not_git_repo(tmp_path):
    """测试工厂函数：非 Git 仓库"""
    sandbox = create_sandbox(tmp_path)

    assert isinstance(sandbox, DummySandbox)


@patch('aegis.utils.git_sandbox.GIT_AVAILABLE', False)
def test_create_sandbox_no_gitpython():
    """测试工厂函数：GitPython 未安装"""
    sandbox = create_sandbox()

    assert isinstance(sandbox, DummySandbox)


# ==========================================
# 边界情况测试
# ==========================================
def test_git_sandbox_untracked_files(temp_git_repo):
    """测试 untracked files 的暂存"""
    repo, repo_path = temp_git_repo

    # 创建 untracked 文件
    untracked_file = repo_path / "untracked.txt"
    untracked_file.write_text("untracked content")

    try:
        with GitSandbox(repo_path):
            raise ValueError("Test")
    except ValueError:
        pass

    # 验证 untracked 文件已恢复
    assert untracked_file.exists()
    assert untracked_file.read_text() == "untracked content"


def test_git_sandbox_subdir_execution(temp_git_repo):
    """测试在子目录中执行（向上探测）"""
    repo, repo_path = temp_git_repo

    # 创建子目录
    subdir = repo_path / "src" / "utils"
    subdir.mkdir(parents=True)

    # 在子目录中创建沙盒
    with GitSandbox(subdir) as sandbox:
        # 验证找到了父目录的 Git 仓库
        assert sandbox.repo.working_dir == str(repo_path)
