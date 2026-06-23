"""
🛡️ Aegis - Code Mapper (AST 特征提取器)
将大型源码文件压缩为包含跨函数引用的"骨架描述"
目标：5000 行代码 -> 500 行骨架 (10% 压缩率)
"""

import re
from pathlib import Path
from typing import List, Dict, Optional, Set, Tuple
from dataclasses import dataclass, field
from enum import Enum
from loguru import logger

try:
    import tree_sitter
    import tree_sitter_python as tspython
    import tree_sitter_javascript as tsjavascript
    import tree_sitter_typescript as tstypescript
    TREE_SITTER_AVAILABLE = True
except ImportError:
    TREE_SITTER_AVAILABLE = False
    logger.warning("tree-sitter 未安装，将使用正则表达式降级方案")


class Language(Enum):
    """支持的编程语言"""
    PYTHON = "python"
    JAVASCRIPT = "javascript"
    TYPESCRIPT = "typescript"
    UNKNOWN = "unknown"


@dataclass
class FunctionInfo:
    """函数/方法信息"""
    name: str
    line_start: int
    line_end: int
    signature: str
    is_async: bool = False
    is_class_method: bool = False
    decorators: List[str] = field(default_factory=list)
    calls: Set[str] = field(default_factory=set)  # 调用的其他函数
    comments: List[str] = field(default_factory=list)  # 函数内的重要注释


@dataclass
class ClassInfo:
    """类信息"""
    name: str
    line_start: int
    line_end: int
    bases: List[str] = field(default_factory=list)  # 继承的基类
    methods: List[FunctionInfo] = field(default_factory=list)
    decorators: List[str] = field(default_factory=list)


@dataclass
class ImportInfo:
    """导入信息"""
    module: str
    names: List[str] = field(default_factory=list)  # 导入的具体名称
    is_relative: bool = False


@dataclass
class CodeSkeleton:
    """代码骨架（压缩后的代码结构）"""
    file_path: Path
    language: Language
    total_lines: int
    skeleton_lines: int
    compression_ratio: float

    imports: List[ImportInfo] = field(default_factory=list)
    classes: List[ClassInfo] = field(default_factory=list)
    functions: List[FunctionInfo] = field(default_factory=list)
    global_comments: List[Tuple[int, str]] = field(default_factory=list)  # (行号, 注释内容)

    def to_markdown(self, max_function_lines: int = 100, context_lines: int = 10) -> str:
        """
        将骨架转换为 Markdown 格式

        Args:
            max_function_lines: 超过此行数的函数将被截断
            context_lines: 截断时保留的头尾行数

        Returns:
            Markdown 格式的骨架描述
        """
        lines = []

        # 文件头
        lines.append(f"# 📄 {self.file_path.name}")
        lines.append(f"**语言**: {self.language.value}")
        lines.append(f"**原始行数**: {self.total_lines}")
        lines.append(f"**骨架行数**: {self.skeleton_lines}")
        lines.append(f"**压缩率**: {self.compression_ratio:.1%}")
        lines.append("")

        # 导入语句
        if self.imports:
            lines.append("## 📦 导入依赖")
            lines.append("```python")
            for imp in self.imports:
                if imp.names:
                    lines.append(f"from {imp.module} import {', '.join(imp.names)}")
                else:
                    lines.append(f"import {imp.module}")
            lines.append("```")
            lines.append("")

        # 全局重要注释
        if self.global_comments:
            lines.append("## 💬 重要注释")
            for line_no, comment in self.global_comments:
                lines.append(f"- L{line_no}: {comment}")
            lines.append("")

        # 类定义
        if self.classes:
            lines.append("## 🏛️ 类定义")
            for cls in self.classes:
                lines.append(f"### `{cls.name}`")
                if cls.bases:
                    lines.append(f"**继承**: {', '.join(cls.bases)}")
                if cls.decorators:
                    lines.append(f"**装饰器**: {', '.join(cls.decorators)}")
                lines.append(f"**位置**: L{cls.line_start}-L{cls.line_end}")

                if cls.methods:
                    lines.append("**方法**:")
                    for method in cls.methods:
                        lines.append(f"- `{method.name}` (L{method.line_start}-L{method.line_end})")
                        if method.calls:
                            lines.append(f"  - 调用: {', '.join(list(method.calls)[:5])}")
                lines.append("")

        # 顶级函数
        if self.functions:
            lines.append("## 🔧 顶级函数")
            for func in self.functions:
                lines.append(f"### `{func.name}`")
                lines.append(f"```python")
                lines.append(func.signature)
                lines.append(f"```")
                lines.append(f"**位置**: L{func.line_start}-L{func.line_end}")

                if func.decorators:
                    lines.append(f"**装饰器**: {', '.join(func.decorators)}")
                if func.is_async:
                    lines.append("**异步**: ✓")
                if func.calls:
                    lines.append(f"**调用函数**: {', '.join(list(func.calls)[:10])}")
                if func.comments:
                    lines.append(f"**内部注释**: {len(func.comments)} 条")
                    for comment in func.comments[:3]:
                        lines.append(f"  - {comment}")
                lines.append("")

        return "\n".join(lines)


class CodeMapper:
    """
    代码映射器 - AST 特征提取的核心引擎
    """

    def __init__(
        self,
        max_function_lines: int = 100,
        context_lines: int = 10,
        preserve_comments: List[str] = None,
    ):
        """
        Args:
            max_function_lines: 超过此行数的函数将被截断
            context_lines: 截断时保留的头尾行数
            preserve_comments: 需要保留的注释标记（如 TODO, FIXME）
        """
        self.max_function_lines = max_function_lines
        self.context_lines = context_lines
        self.preserve_comments = preserve_comments or ["TODO", "FIXME", "HACK", "XXX", "NOTE"]

        # 初始化 tree-sitter 解析器
        self.parsers = {}
        if TREE_SITTER_AVAILABLE:
            self._init_parsers()

    def map_repository(self, repo_path: Path, extensions: List[str] = None) -> List[CodeSkeleton]:
        """
        扫描仓库并提取所有代码骨架

        Args:
            repo_path: 仓库根目录
            extensions: 要扫描的文件扩展名（如 ['.py', '.js']）

        Returns:
            CodeSkeleton 列表
        """
        if extensions is None:
            extensions = ['.py', '.js', '.ts', '.jsx', '.tsx']

        skeletons = []
        for ext in extensions:
            for file_path in repo_path.rglob(f'*{ext}'):
                # 跳过隐藏文件和常见忽略目录
                if any(part.startswith('.') or part in ['node_modules', '__pycache__', 'venv', 'dist', 'build']
                       for part in file_path.parts):
                    continue

                skeleton = self.extract_skeleton(file_path)
                if skeleton:
                    skeletons.append(skeleton)

        return skeletons

    def _init_parsers(self):
        """初始化 tree-sitter 解析器"""
        try:
            # Python
            self.parsers[Language.PYTHON] = tree_sitter.Parser()
            self.parsers[Language.PYTHON].language = tree_sitter.Language(tspython.language())

            # JavaScript
            self.parsers[Language.JAVASCRIPT] = tree_sitter.Parser()
            self.parsers[Language.JAVASCRIPT].language = tree_sitter.Language(tsjavascript.language())

            # TypeScript - 注意: tree-sitter-typescript 有不同的 API
            try:
                from tree_sitter_typescript import language_typescript
                self.parsers[Language.TYPESCRIPT] = tree_sitter.Parser()
                self.parsers[Language.TYPESCRIPT].language = tree_sitter.Language(language_typescript())
            except (ImportError, AttributeError):
                logger.warning("TypeScript 解析器初始化失败，将跳过 .ts 文件")

            logger.success("tree-sitter 解析器初始化成功")
        except Exception as e:
            logger.error(f"tree-sitter 初始化失败: {e}")
            import traceback
            logger.error(traceback.format_exc())

    def detect_language(self, file_path: Path) -> Language:
        """根据文件扩展名检测语言"""
        suffix = file_path.suffix.lower()
        if suffix == ".py":
            return Language.PYTHON
        elif suffix in [".js", ".jsx"]:
            return Language.JAVASCRIPT
        elif suffix in [".ts", ".tsx"]:
            return Language.TYPESCRIPT
        else:
            return Language.UNKNOWN

    def extract_skeleton(self, file_path: Path) -> Optional[CodeSkeleton]:
        """
        提取代码骨架

        Args:
            file_path: 源码文件路径

        Returns:
            CodeSkeleton 或 None（如果解析失败）
        """
        if not file_path.exists():
            logger.error(f"文件不存在: {file_path}")
            return None

        language = self.detect_language(file_path)
        if language == Language.UNKNOWN:
            logger.warning(f"不支持的语言: {file_path}")
            return None

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                code = f.read()
        except Exception as e:
            logger.error(f"读取文件失败: {file_path} - {e}")
            return None

        # 尝试使用 tree-sitter 解析
        if TREE_SITTER_AVAILABLE and language in self.parsers:
            return self._extract_with_treesitter(file_path, code, language)
        else:
            # 降级到正则表达式方案
            return self._extract_with_regex(file_path, code, language)

    def _extract_with_treesitter(
        self,
        file_path: Path,
        code: str,
        language: Language
    ) -> CodeSkeleton:
        """使用 tree-sitter 提取骨架（最精确的方法）"""
        parser = self.parsers[language]
        tree = parser.parse(bytes(code, "utf8"))
        root_node = tree.root_node

        skeleton = CodeSkeleton(
            file_path=file_path,
            language=language,
            total_lines=code.count('\n') + 1,
            skeleton_lines=0,
            compression_ratio=0.0
        )

        lines = code.split('\n')

        # 根据语言选择不同的提取策略
        if language == Language.PYTHON:
            self._extract_python_ast(root_node, lines, skeleton)
        elif language in [Language.JAVASCRIPT, Language.TYPESCRIPT]:
            self._extract_js_ast(root_node, lines, skeleton)

        # 计算压缩率
        skeleton_content = skeleton.to_markdown()
        skeleton.skeleton_lines = skeleton_content.count('\n') + 1
        skeleton.compression_ratio = skeleton.skeleton_lines / max(skeleton.total_lines, 1)

        return skeleton

    def _extract_python_ast(
        self,
        root_node,
        lines: List[str],
        skeleton: CodeSkeleton
    ):
        """提取 Python AST 信息"""

        def visit_node(node, parent_class: Optional[str] = None):
            """递归访问 AST 节点"""

            # 提取导入语句
            if node.type == "import_statement":
                module = node.child_by_field_name("name")
                if module:
                    skeleton.imports.append(ImportInfo(module=module.text.decode("utf8")))

            elif node.type == "import_from_statement":
                module = node.child_by_field_name("module_name")
                if module:
                    imp = ImportInfo(module=module.text.decode("utf8"), is_relative=True)
                    # 提取导入的名称
                    for child in node.children:
                        if child.type == "dotted_name":
                            imp.names.append(child.text.decode("utf8"))
                    skeleton.imports.append(imp)

            # 提取类定义
            elif node.type == "class_definition":
                cls_name_node = node.child_by_field_name("name")
                if cls_name_node:
                    cls_info = ClassInfo(
                        name=cls_name_node.text.decode("utf8"),
                        line_start=node.start_point[0] + 1,
                        line_end=node.end_point[0] + 1
                    )

                    # 提取基类
                    superclasses = node.child_by_field_name("superclasses")
                    if superclasses:
                        for child in superclasses.children:
                            if child.type == "identifier":
                                cls_info.bases.append(child.text.decode("utf8"))

                    skeleton.classes.append(cls_info)

                    # 递归提取类中的方法
                    for child in node.children:
                        visit_node(child, parent_class=cls_info.name)

            # 提取函数定义
            elif node.type == "function_definition":
                func_name_node = node.child_by_field_name("name")
                if func_name_node:
                    func_name = func_name_node.text.decode("utf8")
                    line_start = node.start_point[0] + 1
                    line_end = node.end_point[0] + 1

                    # 提取函数签名
                    signature_lines = lines[line_start - 1:min(line_start + 2, len(lines))]
                    signature = "\n".join(signature_lines).strip()

                    func_info = FunctionInfo(
                        name=func_name,
                        line_start=line_start,
                        line_end=line_end,
                        signature=signature,
                        is_class_method=(parent_class is not None)
                    )

                    # 提取函数内的函数调用
                    self._extract_function_calls(node, func_info)

                    # 提取函数内的重要注释
                    self._extract_function_comments(node, lines, func_info)

                    # 添加到对应的容器
                    if parent_class:
                        # 添加到类的方法列表
                        for cls in skeleton.classes:
                            if cls.name == parent_class:
                                cls.methods.append(func_info)
                                break
                    else:
                        skeleton.functions.append(func_info)

            # 提取全局注释
            elif node.type == "comment":
                comment_text = node.text.decode("utf8").strip()
                for marker in self.preserve_comments:
                    if marker in comment_text:
                        skeleton.global_comments.append((node.start_point[0] + 1, comment_text))
                        break

            # 递归处理子节点
            for child in node.children:
                visit_node(child, parent_class)

        visit_node(root_node)

    def _extract_function_calls(self, func_node, func_info: FunctionInfo):
        """提取函数内的所有函数调用"""
        def visit(node):
            if node.type == "call":
                func_name_node = node.child_by_field_name("function")
                if func_name_node:
                    func_name = func_name_node.text.decode("utf8")
                    # 只保留简单的函数名（去掉模块前缀）
                    if '.' in func_name:
                        func_name = func_name.split('.')[-1]
                    func_info.calls.add(func_name)

            for child in node.children:
                visit(child)

        visit(func_node)

    def _extract_function_comments(self, func_node, lines: List[str], func_info: FunctionInfo):
        """提取函数内的重要注释"""
        def visit(node):
            if node.type == "comment":
                comment_text = node.text.decode("utf8").strip()
                for marker in self.preserve_comments:
                    if marker in comment_text:
                        func_info.comments.append(comment_text)
                        break

            for child in node.children:
                visit(child)

        visit(func_node)

    def _extract_js_ast(
        self,
        root_node,
        lines: List[str],
        skeleton: CodeSkeleton
    ):
        """提取 JavaScript/TypeScript AST 信息（简化版）"""
        logger.info("JavaScript/TypeScript 使用正则降级方案进行 AST 提取")
        self._extract_with_regex_impl(lines, skeleton, language='js')

    def _extract_with_regex(
        self,
        file_path: Path,
        code: str,
        language: Language
    ) -> CodeSkeleton:
        """使用正则表达式提取骨架（降级方案）"""
        skeleton = CodeSkeleton(
            file_path=file_path,
            language=language,
            total_lines=code.count('\n') + 1,
            skeleton_lines=0,
            compression_ratio=0.0
        )

        lines = code.split('\n')
        self._extract_with_regex_impl(lines, skeleton)

        # 计算压缩率
        skeleton_content = skeleton.to_markdown()
        skeleton.skeleton_lines = skeleton_content.count('\n') + 1
        skeleton.compression_ratio = skeleton.skeleton_lines / max(skeleton.total_lines, 1)

        return skeleton

    def _extract_with_regex_impl(self, lines: List[str], skeleton: CodeSkeleton, language: str = 'python'):
        """
        正则表达式提取实现（支持多语言）

        Args:
            lines: 代码行列表
            skeleton: 要填充的骨架对象
            language: 语言类型 ('python' 或 'js')
        """
        if language == 'python':
            # Python 导入语句
            import_pattern = re.compile(r'^(import|from)\s+[\w.]+')
            # Python 函数定义
            func_pattern = re.compile(r'^(async\s+)?def\s+(\w+)\s*\(')
            # Python 类定义
            class_pattern = re.compile(r'^class\s+(\w+)')
            # Python 注释
            comment_pattern = re.compile(r'#\s*(' + '|'.join(self.preserve_comments) + r')[:\s]')
        else:  # JavaScript/TypeScript
            # JS/TS 导入语句 (import ... from '...')
            import_pattern = re.compile(r'^import\s+.*from\s+[\'"]')
            # JS/TS 函数定义 (function xxx, const xxx = () =>, async function)
            func_pattern = re.compile(r'^(async\s+)?(function\s+(\w+)|const\s+(\w+)\s*=.*?=>|(\w+)\s*:\s*\([^)]*\)\s*=>)')
            # JS/TS 类定义
            class_pattern = re.compile(r'^(export\s+)?(class|interface)\s+(\w+)')
            # JS/TS 注释 (// 或 /*)
            comment_pattern = re.compile(r'(//|/\*)\s*(' + '|'.join(self.preserve_comments) + r')[:\s]')

        current_class = None

        for i, line in enumerate(lines, start=1):
            stripped = line.strip()

            # 提取导入
            if import_pattern.match(stripped):
                skeleton.imports.append(ImportInfo(module=stripped))

            # 提取类
            class_match = class_pattern.match(stripped)
            if class_match:
                if language == 'python':
                    cls_name = class_match.group(1)
                else:  # JS/TS
                    cls_name = class_match.group(3)
                current_class = ClassInfo(
                    name=cls_name,
                    line_start=i,
                    line_end=i  # 暂时设置，后续更新
                )
                skeleton.classes.append(current_class)

            # 提取函数
            func_match = func_pattern.match(stripped)
            if func_match:
                if language == 'python':
                    is_async = func_match.group(1) is not None
                    func_name = func_match.group(2)
                else:  # JS/TS
                    is_async = func_match.group(1) is not None
                    # 尝试多个捕获组（function name, const name, arrow function name）
                    func_name = func_match.group(3) or func_match.group(4) or func_match.group(5) or 'anonymous'

                func_info = FunctionInfo(
                    name=func_name,
                    line_start=i,
                    line_end=i,  # 暂时设置
                    signature=stripped,
                    is_async=is_async,
                    is_class_method=(current_class is not None)
                )

                if current_class:
                    current_class.methods.append(func_info)
                else:
                    skeleton.functions.append(func_info)

            # 提取重要注释
            if comment_pattern.search(stripped):
                skeleton.global_comments.append((i, stripped))


async def map_codebase(
    root_path: Path,
    ignore_dirs: List[str],
    max_function_lines: int = 100,
    context_lines: int = 10,
    preserve_comments: List[str] = None
) -> List[CodeSkeleton]:
    """
    映射整个代码库（外部调用入口）

    Args:
        root_path: 项目根目录
        ignore_dirs: 要忽略的目录列表
        max_function_lines: 函数最大行数
        context_lines: 上下文行数
        preserve_comments: 保留的注释标记

    Returns:
        代码骨架列表
    """
    mapper = CodeMapper(
        max_function_lines=max_function_lines,
        context_lines=context_lines,
        preserve_comments=preserve_comments
    )

    skeletons = []
    ignore_set = set(ignore_dirs)

    logger.info(f"开始映射代码库: {root_path}")

    # 支持的文件扩展名
    supported_extensions = {".py", ".js", ".jsx", ".ts", ".tsx"}

    for file_path in root_path.rglob("*"):
        # 跳过忽略目录
        if any(part in ignore_set for part in file_path.parts):
            continue

        # 只处理支持的文件
        if file_path.suffix in supported_extensions and file_path.is_file():
            logger.debug(f"提取: {file_path}")
            skeleton = mapper.extract_skeleton(file_path)
            if skeleton:
                skeletons.append(skeleton)
                logger.info(
                    f"  ✓ {file_path.name}: {skeleton.total_lines} 行 -> "
                    f"{skeleton.skeleton_lines} 行 (压缩率: {skeleton.compression_ratio:.1%})"
                )

    logger.success(f"代码映射完成！共处理 {len(skeletons)} 个文件")
    return skeletons
