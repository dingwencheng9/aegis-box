"""
🛡️ Aegis - Git Sandbox（Git 沙盒）
基于上下文管理器的安全补丁环境，支持异常回滚
"""

from pathlib import Path
from typing import Optional
from datetime import datetime
from loguru import logger

try:
    import git
    from git.exc import InvalidGitRepositoryError, GitCommandError
    GIT_AVAILABLE = True
except ImportError:
    GIT_AVAILABLE = False
    logger.warning("GitPython 未安装，Git 沙盒功能将被禁用")


# ==========================================
# 异常定义
# ==========================================
class SandboxError(Exception):
    """沙盒操作失败异常"""
    pass


# ==========================================
# Git 沙盒（完整实现）
# ==========================================
class GitSandbox:
    """
    Git 沙盒上下文管理器

    职责：
    1. 进入时：保护工作区（stash + 创建补丁分支）
    2. 退出时：异常回滚 or 成功提交
    3. 确保用户工作区永不损坏

    Example:
        >>> with GitSandbox(auto_commit=True):
        ...     apply_patches(source, patches)  # 可能失败
        >>> # 如果成功：补丁已提交到新分支
        >>> # 如果失败：工作区完全恢复原状
    """

    def __init__(
        self,
        repo_path: Optional[Path] = None,
        auto_commit: bool = False,
        commit_message: Optional[str] = None
    ):
        """
        初始化 Git 沙盒

        Args:
            repo_path: Git 仓库路径（默认当前目录）
            auto_commit: 是否自动提交成功的补丁
            commit_message: 提交消息（可选）
        """
        self.repo_path = repo_path or Path.cwd()
        self.auto_commit = auto_commit
        self.commit_message = commit_message or "feat: Apply Aegis patches"

        # 状态记录（在 __enter__ 中填充）
        self.repo: Optional[git.Repo] = None
        self.original_branch_name: Optional[str] = None
        self.patch_branch_name: Optional[str] = None
        self.stashed: bool = False
        self.is_detached: bool = False

    def __enter__(self) -> "GitSandbox":
        """
        进入沙盒：保护工作区

        步骤：
        1. 检查是否为 Git 仓库（向上探测）
        2. 记录当前分支（处理 Detached HEAD）
        3. 如果有未提交更改 -> git stash -u（含 untracked files）
        4. 创建补丁分支 aegis-patch-{timestamp}
        5. 切换到补丁分支

        Returns:
            self

        Raises:
            SandboxError: Git 操作失败
        """
        logger.info("🛡️  进入 Git 沙盒...")

        # Step 1: 检查是否为 Git 仓库（地雷 1：向上探测）
        try:
            self.repo = git.Repo(
                self.repo_path,
                search_parent_directories=True
            )
            logger.debug(f"✅ Git 仓库已找到: {self.repo.working_dir}")
        except (InvalidGitRepositoryError, git.NoSuchPathError) as e:
            logger.error(f"❌ {self.repo_path} 不是 Git 仓库")
            raise SandboxError(f"{self.repo_path} 不是 Git 仓库") from e

        # Step 2: 记录当前分支（地雷 2：处理 Detached HEAD）
        try:
            self.original_branch_name = self.repo.active_branch.name
            self.is_detached = False
            logger.debug(f"当前分支: {self.original_branch_name}")
        except TypeError:
            # Detached HEAD 状态会抛出 TypeError
            self.original_branch_name = self.repo.head.commit.hexsha
            self.is_detached = True
            logger.warning(
                f"⚠️  当前处于 Detached HEAD 状态 "
                f"(commit: {self.original_branch_name[:7]})"
            )

        # Step 3: 检查工作区状态并暂存
        if self.repo.is_dirty(untracked_files=True):
            logger.info("📦 检测到未提交的更改，正在暂存...")
            self._stash_changes()
        else:
            logger.debug("✅ 工作区干净，无需暂存")

        # Step 4: 创建补丁分支（防御性验证）
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        self.patch_branch_name = f"aegis-patch-{timestamp}"

        # Security: 验证分支名只包含安全字符
        import re
        if not re.match(r'^[a-zA-Z0-9/_-]+$', self.patch_branch_name):
            logger.error(f"🚨 非法分支名: {self.patch_branch_name}")
            if self.stashed:
                self._restore_stash()
            raise SandboxError(f"Invalid branch name: {self.patch_branch_name}")

        try:
            new_branch = self.repo.create_head(self.patch_branch_name)
            logger.info(f"✅ 创建补丁分支: {self.patch_branch_name}")
        except GitCommandError as e:
            logger.error(f"❌ 创建分支失败: {e}")
            # 如果创建失败，恢复 stash
            if self.stashed:
                self._restore_stash()
            raise SandboxError(f"创建分支失败: {e}") from e

        # Step 5: 切换到补丁分支
        try:
            new_branch.checkout()
            logger.info(f"🔀 已切换到补丁分支: {self.patch_branch_name}")
        except GitCommandError as e:
            logger.error(f"❌ 切换分支失败: {e}")
            # 清理：删除刚创建的分支并恢复 stash
            try:
                self.repo.delete_head(self.patch_branch_name, force=True)
            except Exception:
                pass
            if self.stashed:
                self._restore_stash()
            raise SandboxError(f"切换分支失败: {e}") from e

        logger.success("🎯 沙盒已就绪，可以安全地应用补丁")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        """
        退出沙盒：异常回滚 or 成功提交

        Args:
            exc_type: 异常类型
            exc_val: 异常值
            exc_tb: 异常堆栈

        Returns:
            False（让异常继续传播）
        """
        if exc_type is not None:
            # 异常分支：回滚
            logger.error(f"❌ 检测到异常: {exc_type.__name__}: {exc_val}")
            self._rollback()
        else:
            # 成功分支：提交或保留
            self._finalize()

        return False  # 让异常继续传播

    def _stash_changes(self):
        """
        暂存当前工作区（地雷 3：含 untracked files）

        使用原生 git stash 命令，确保 untracked files 也被暂存

        Raises:
            SandboxError: stash 失败
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        stash_msg = f"aegis-backup-{timestamp}"

        try:
            # 地雷 3：使用 -u 参数暂存 untracked files
            self.repo.git.stash('push', '-u', '-m', stash_msg)
            self.stashed = True
            logger.success(f"✅ 工作区已暂存: {stash_msg}")
        except GitCommandError as e:
            logger.error(f"❌ 暂存失败: {e}")
            raise SandboxError(f"暂存失败: {e}") from e

    def _restore_stash(self):
        """恢复 stash（内部辅助方法）"""
        if not self.stashed:
            return

        try:
            self.repo.git.stash('pop')
            self.stashed = False
            logger.success("✅ 工作区已恢复")
        except GitCommandError as e:
            logger.error(f"⚠️  stash pop 失败: {e}")
            logger.info("提示：您可以手动执行 'git stash list' 查看暂存")

    def _rollback(self):
        """
        回滚沙盒：清除补丁并恢复原状

        步骤：
        1. git reset --hard HEAD（清除损坏补丁）
        2. 切换回原分支
        3. git stash pop（恢复用户更改）
        4. 删除补丁分支
        """
        logger.warning("🔄 开始回滚沙盒...")

        try:
            # Step 1: 硬重置（清除损坏的补丁）
            logger.info("⏪ 执行 git reset --hard HEAD...")
            self.repo.git.reset('--hard', 'HEAD')
            logger.debug("✅ 补丁已清除")

            # Step 2: 切换回原分支
            logger.info(f"🔀 切换回原分支: {self.original_branch_name}")
            if self.is_detached:
                # Detached HEAD：直接切换到 commit
                self.repo.git.checkout(self.original_branch_name)
            else:
                # 普通分支：通过分支名切换
                self.repo.heads[self.original_branch_name].checkout()
            logger.debug("✅ 已切换回原分支")

            # Step 3: 恢复 stash
            if self.stashed:
                logger.info("📦 恢复工作区...")
                self._restore_stash()

            # Step 4: 删除补丁分支
            if self.patch_branch_name:
                logger.info(f"🗑️  删除补丁分支: {self.patch_branch_name}")
                try:
                    self.repo.delete_head(self.patch_branch_name, force=True)
                    logger.debug("✅ 补丁分支已删除")
                except GitCommandError as e:
                    logger.warning(f"⚠️  删除分支失败: {e}")

            logger.success("🎯 回滚完成！工作区已安全恢复")

        except Exception as e:
            logger.critical(f"❌ 回滚过程中出现严重错误: {e}")
            logger.info("请手动检查 Git 状态并恢复工作区")
            logger.info(f"原分支: {self.original_branch_name}")
            if self.stashed:
                logger.info("未提交更改已暂存，可执行 'git stash list' 查看")

    def _finalize(self):
        """
        完成沙盒：自动提交或保留分支

        如果 auto_commit=True：
        1. 检查是否有改动（地雷 4：防止空提交）
        2. git add -A
        3. git commit
        4. 打印成功日志

        如果 auto_commit=False：
        1. 保留在补丁分支
        2. 提示用户检查差异
        """
        logger.info("✅ 补丁应用成功！")

        # 地雷 4：检查是否有改动（防止空提交）
        if not self.repo.is_dirty(untracked_files=True):
            logger.info("ℹ️  没有检测到任何文件改动，跳过提交")
            logger.info(f"当前分支: {self.patch_branch_name}")
            return

        if self.auto_commit:
            logger.info("🚀 自动提交补丁...")

            try:
                # git add -A
                self.repo.git.add('-A')
                logger.debug("✅ 已暂存所有更改")

                # git commit
                self.repo.index.commit(self.commit_message)
                logger.success(f"✅ 补丁已提交: {self.commit_message}")
                logger.info(f"📍 当前分支: {self.patch_branch_name}")
                logger.info(
                    f"💡 提示：使用 'git diff {self.original_branch_name}' 查看差异"
                )

            except GitCommandError as e:
                logger.error(f"❌ 提交失败: {e}")
                logger.info(f"补丁已应用但未提交，当前分支: {self.patch_branch_name}")

        else:
            logger.info(f"📍 补丁已应用到分支: {self.patch_branch_name}")
            logger.info(
                f"💡 提示：使用 'git diff {self.original_branch_name}' 查看差异"
            )
            logger.info(
                f"💡 提示：满意后可以执行 'git checkout {self.original_branch_name} "
                f"&& git merge {self.patch_branch_name}'"
            )


# ==========================================
# 空实现沙盒（非 Git 仓库降级）
# ==========================================
class DummySandbox:
    """
    空实现沙盒（非 Git 仓库时使用）

    职责：
    1. 打印警告信息
    2. 不执行任何 Git 操作
    3. 不阻塞工作流

    Example:
        >>> with DummySandbox():
        ...     apply_patches(source, patches)
        >>> # 正常执行，但没有回滚能力
    """

    def __init__(
        self,
        repo_path: Optional[Path] = None,
        auto_commit: bool = False,
        commit_message: Optional[str] = None
    ):
        """
        初始化空沙盒

        Args:
            repo_path: 仓库路径（忽略）
            auto_commit: 是否自动提交（忽略）
            commit_message: 提交消息（忽略）
        """
        self.repo_path = repo_path or Path.cwd()

    def __enter__(self) -> "DummySandbox":
        """进入空沙盒（仅打印警告）"""
        logger.warning("⚠️  当前目录不是 Git 仓库，沙盒保护已禁用")
        logger.info("💡 提示：初始化 Git 仓库可启用自动回滚功能")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        """退出空沙盒（无操作）"""
        if exc_type is not None:
            logger.error(f"❌ 检测到异常: {exc_type.__name__}: {exc_val}")
            logger.warning("⚠️  由于非 Git 仓库，无法自动回滚")
        else:
            logger.success("✅ 补丁应用成功（未使用 Git 保护）")

        return False  # 让异常继续传播


# ==========================================
# 工厂函数：自动选择沙盒类型
# ==========================================
def create_sandbox(
    repo_path: Optional[Path] = None,
    auto_commit: bool = False,
    commit_message: Optional[str] = None
):
    """
    自动选择沙盒类型（Git vs Dummy）

    Args:
        repo_path: Git 仓库路径（默认当前目录）
        auto_commit: 是否自动提交成功的补丁
        commit_message: 提交消息（可选）

    Returns:
        GitSandbox 或 DummySandbox

    Example:
        >>> with create_sandbox(auto_commit=True) as sandbox:
        ...     apply_patches(source, patches)
    """
    if not GIT_AVAILABLE:
        logger.warning("⚠️  GitPython 未安装，使用 DummySandbox")
        return DummySandbox(repo_path, auto_commit, commit_message)

    repo_path = repo_path or Path.cwd()

    # 检查是否为 Git 仓库（向上探测）
    try:
        git.Repo(repo_path, search_parent_directories=True)
        return GitSandbox(repo_path, auto_commit, commit_message)
    except (InvalidGitRepositoryError, git.NoSuchPathError):
        logger.debug(f"{repo_path} 不是 Git 仓库，使用 DummySandbox")
        return DummySandbox(repo_path, auto_commit, commit_message)
