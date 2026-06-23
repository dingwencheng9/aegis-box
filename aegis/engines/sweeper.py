"""
🛡️ Aegis - Asset Sweeper (资产清道夫)
高效的多线程/异步文件扫描与清理引擎
"""

import asyncio
from pathlib import Path
from typing import List, Set, Dict, Optional
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor
from loguru import logger
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn


@dataclass
class ScanResult:
    """扫描结果数据类"""
    total_files: int = 0
    total_dirs: int = 0
    total_size: int = 0  # 字节
    ignorable_files: List[Path] = None
    ignorable_dirs: List[Path] = None
    ignorable_size: int = 0

    def __post_init__(self):
        if self.ignorable_files is None:
            self.ignorable_files = []
        if self.ignorable_dirs is None:
            self.ignorable_dirs = []

    @property
    def ignorable_size_mb(self) -> float:
        """可忽略文件的总大小（MB）"""
        return self.ignorable_size / (1024 * 1024)

    @property
    def total_size_mb(self) -> float:
        """总大小（MB）"""
        return self.total_size / (1024 * 1024)


class AssetSweeper:
    """
    资产清道夫引擎
    职责：
    1. 高速扫描项目目录
    2. 识别垃圾文件（node_modules, __pycache__, .git 等）
    3. 计算可节省的磁盘空间
    4. 提供安全删除功能
    """

    def __init__(
        self,
        ignore_dirs: List[str],
        ignore_extensions: List[str],
        max_workers: int = 4,
    ):
        """
        Args:
            ignore_dirs: 要忽略的目录名列表
            ignore_extensions: 要忽略的文件扩展名列表
            max_workers: 最大并发线程数
        """
        self.ignore_dirs = set(ignore_dirs)
        self.ignore_extensions = set(ignore_extensions)
        self.max_workers = max_workers

    def should_ignore_dir(self, dir_path: Path) -> bool:
        """判断目录是否应该被忽略"""
        return dir_path.name in self.ignore_dirs

    def should_ignore_file(self, file_path: Path) -> bool:
        """判断文件是否应该被忽略"""
        return file_path.suffix in self.ignore_extensions

    def scan_directory(self, root_path: Path) -> ScanResult:
        """
        扫描目录（同步版本，用于线程池）

        Args:
            root_path: 要扫描的根目录

        Returns:
            ScanResult: 扫描结果
        """
        result = ScanResult()

        try:
            for item in root_path.iterdir():
                # 跳过符号链接
                if item.is_symlink():
                    continue

                # 处理目录
                if item.is_dir():
                    result.total_dirs += 1

                    # 检查是否是需要忽略的目录
                    if self.should_ignore_dir(item):
                        result.ignorable_dirs.append(item)
                        # 计算目录大小
                        dir_size = self._calculate_dir_size(item)
                        result.ignorable_size += dir_size
                        logger.debug(f"忽略目录: {item} (大小: {dir_size / 1024 / 1024:.2f} MB)")
                    else:
                        # 递归扫描子目录
                        sub_result = self.scan_directory(item)
                        result.total_files += sub_result.total_files
                        result.total_dirs += sub_result.total_dirs
                        result.total_size += sub_result.total_size
                        result.ignorable_files.extend(sub_result.ignorable_files)
                        result.ignorable_dirs.extend(sub_result.ignorable_dirs)
                        result.ignorable_size += sub_result.ignorable_size

                # 处理文件
                elif item.is_file():
                    result.total_files += 1
                    file_size = item.stat().st_size
                    result.total_size += file_size

                    # 检查是否是需要忽略的文件
                    if self.should_ignore_file(item):
                        result.ignorable_files.append(item)
                        result.ignorable_size += file_size
                        logger.debug(f"忽略文件: {item} (大小: {file_size / 1024:.2f} KB)")

        except PermissionError as e:
            logger.warning(f"权限错误，跳过: {root_path} - {e}")
        except Exception as e:
            logger.error(f"扫描错误: {root_path} - {e}")

        return result

    def _calculate_dir_size(self, dir_path: Path) -> int:
        """
        计算目录的总大小（字节）

        Args:
            dir_path: 目录路径

        Returns:
            总大小（字节）
        """
        total_size = 0
        try:
            for item in dir_path.rglob('*'):
                if item.is_file() and not item.is_symlink():
                    try:
                        total_size += item.stat().st_size
                    except (PermissionError, FileNotFoundError):
                        pass
        except Exception as e:
            logger.warning(f"计算目录大小失败: {dir_path} - {e}")
        return total_size

    async def scan_async(self, root_path: Path) -> ScanResult:
        """
        异步扫描（使用线程池执行同步扫描）

        Args:
            root_path: 要扫描的根目录

        Returns:
            ScanResult: 扫描结果
        """
        loop = asyncio.get_event_loop()
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            result = await loop.run_in_executor(
                executor,
                self.scan_directory,
                root_path
            )
        return result

    def clean(
        self,
        result: ScanResult,
        dry_run: bool = True,
        confirm: bool = True
    ) -> int:
        """
        清理垃圾文件

        Args:
            result: 扫描结果
            dry_run: 仅预览，不实际删除
            confirm: 是否需要用户确认

        Returns:
            删除的字节数
        """
        if dry_run:
            logger.info("【Dry Run 模式】预览要删除的文件：")
            for dir_path in result.ignorable_dirs:
                logger.info(f"  - [DIR] {dir_path}")
            for file_path in result.ignorable_files:
                logger.info(f"  - [FILE] {file_path}")
            logger.info(f"预计可节省空间: {result.ignorable_size_mb:.2f} MB")
            return 0

        if confirm:
            logger.warning(f"即将删除 {len(result.ignorable_dirs)} 个目录和 {len(result.ignorable_files)} 个文件")
            logger.warning(f"总计: {result.ignorable_size_mb:.2f} MB")
            response = input("确认删除？(yes/no): ")
            if response.lower() != "yes":
                logger.info("已取消删除操作")
                return 0

        deleted_size = 0

        # 删除目录
        for dir_path in result.ignorable_dirs:
            try:
                import shutil
                shutil.rmtree(dir_path)
                logger.success(f"已删除目录: {dir_path}")
            except Exception as e:
                logger.error(f"删除目录失败: {dir_path} - {e}")

        # 删除文件
        for file_path in result.ignorable_files:
            try:
                file_size = file_path.stat().st_size
                file_path.unlink()
                deleted_size += file_size
                logger.success(f"已删除文件: {file_path}")
            except Exception as e:
                logger.error(f"删除文件失败: {file_path} - {e}")

        logger.success(f"清理完成！共释放空间: {deleted_size / 1024 / 1024:.2f} MB")
        return deleted_size


async def sweep_project(
    root_path: Path,
    ignore_dirs: List[str],
    ignore_extensions: List[str],
    dry_run: bool = True,
) -> ScanResult:
    """
    扫描并清理项目（外部调用入口）

    Args:
        root_path: 项目根目录
        ignore_dirs: 要忽略的目录列表
        ignore_extensions: 要忽略的扩展名列表
        dry_run: 是否为预览模式

    Returns:
        ScanResult: 扫描结果
    """
    sweeper = AssetSweeper(
        ignore_dirs=ignore_dirs,
        ignore_extensions=ignore_extensions,
        max_workers=4
    )

    logger.info(f"开始扫描项目: {root_path}")
    result = await sweeper.scan_async(root_path)

    logger.info(f"扫描完成！")
    logger.info(f"  - 总文件数: {result.total_files}")
    logger.info(f"  - 总目录数: {result.total_dirs}")
    logger.info(f"  - 总大小: {result.total_size_mb:.2f} MB")
    logger.info(f"  - 可清理文件数: {len(result.ignorable_files)}")
    logger.info(f"  - 可清理目录数: {len(result.ignorable_dirs)}")
    logger.info(f"  - 可节省空间: {result.ignorable_size_mb:.2f} MB")

    if not dry_run:
        sweeper.clean(result, dry_run=False, confirm=True)

    return result
