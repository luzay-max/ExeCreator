# -*- coding: utf-8 -*-
"""
obfuscator.py — 轻量级代码混淆器

对已合并的 boot.py 进行以下处理：
1. 插入无意义的"垃圾代码"（死分支、哑变量赋值）
2. 将部分关键字符串替换为 bytes.decode() 形式
3. 在模块顶部插入伪造 import（看起来是正常工具库）
4. 对局部变量名进行随机化替换（仅限合并后的 boot 脚本，不影响 CONFIG 等关键名称）

设计原则：
- 只做语法层面的混淆，不依赖任何第三方库（避免引入新依赖）
- 保持代码可运行性（混淆后必须能被 Python 正常解析并执行）
- 随机性：每次构建生成不同的混淆结果，增加特征多样性
"""

import hashlib
import logging
import random
import re
import string

logger = logging.getLogger(__name__)


# ======================================================================= #
#  工具函数
# ======================================================================= #

def _rand_id(length: int = 8, seed: int | None = None) -> str:
    """生成随机标识符（字母开头，字母+数字组成）"""
    rng = random.Random(seed)
    first = rng.choice(string.ascii_lowercase)
    rest = ''.join(rng.choices(string.ascii_lowercase + string.digits, k=length - 1))
    return first + rest


def _encode_string(s: str) -> str:
    """将字符串编码为 bytes literal + decode() 形式，绕过字符串字面值扫描。"""
    encoded = s.encode('utf-8')
    hex_repr = ''.join(f'\\x{b:02x}' for b in encoded)
    return f'b"{hex_repr}".decode()'


def _junk_block(indent: int = 0, seed: int = 0) -> str:
    """
    生成一段无意义的死代码块（永远不会被执行的 if False 分支）。
    包含哑变量赋值、循环、数学运算，增加静态特征多样性。
    """
    pad = ' ' * indent
    rng = random.Random(seed)

    var1 = _rand_id(6, seed)
    var2 = _rand_id(7, seed + 1)
    var3 = _rand_id(5, seed + 2)

    num1 = rng.randint(100, 9999)
    num2 = rng.randint(1, 99)
    num3 = rng.randint(1000, 99999)

    lines = [
        f"{pad}if False:",
        f"{pad}    {var1} = {num1} * {num2} + {num3}",
        f"{pad}    {var2} = [{var1} ^ i for i in range({rng.randint(4,12)})]",
        f"{pad}    {var3} = sum({var2}) // max(len({var2}), 1)",
        f"{pad}    _ = {var3}",
    ]
    return '\n'.join(lines)


# ======================================================================= #
#  主混淆器类
# ======================================================================= #

class CodeObfuscator:
    """
    对已合并的单文件 Python 脚本进行轻量级混淆。

    用法：
        obfuscator = CodeObfuscator()
        obfuscated_code = obfuscator.obfuscate(source_code)
    """

    # 不允许被重命名的保留名称（CONFIG 键、模块级常量、魔术属性等）
    PROTECTED_NAMES = frozenset({
        'CONFIG', 'self', 'cls', 'True', 'False', 'None',
        '__name__', '__file__', '__doc__', '__all__', '__main__',
        'main', 'scan_thread_func', 'log_callback',
        # 重要的公开 API 名称
        'GameScanner', 'FakeLoaderUI', 'SelfUpdater',
        'CacheScanner', 'RegistryScanner', 'DriveScanner',
        'BaseScanner',
        # Python 内置
        'print', 'len', 'range', 'list', 'dict', 'set', 'str', 'int',
        'float', 'bool', 'bytes', 'open', 'type', 'isinstance',
        'hasattr', 'getattr', 'setattr', 'super', 'zip', 'enumerate',
        'map', 'filter', 'sorted', 'reversed', 'sum', 'min', 'max',
        'abs', 'round', 'repr', 'hash', 'id', 'iter', 'next',
        'Exception', 'OSError', 'IOError', 'PermissionError',
        'ValueError', 'TypeError', 'KeyError', 'IndexError',
        'RuntimeError', 'StopIteration', 'AttributeError',
        'UnicodeDecodeError', 'json', 'os', 'sys', 're', 'time',
        'threading', 'datetime', 'webbrowser', 'ctypes', 'winreg',
        'atexit', 'shutil', 'pathlib', 'Path', 'tkinter', 'tk', 'ttk',
        'random', 'base64', 'concurrent',
        # Python 关键字
        'import', 'from', 'as', 'def', 'class', 'return', 'if', 'else', 'elif',
        'for', 'in', 'while', 'try', 'except', 'finally', 'with', 'pass', 'break',
        'continue', 'yield', 'lambda', 'global', 'nonlocal', 'assert', 'del',
        'raise', 'and', 'or', 'not', 'is', 'async', 'await'
    })

    # 混淆目标：仅对这些简单局部变量名重命名
    _LOCAL_VAR_PATTERN = re.compile(r'\b([a-z][a-z_]{2,12})\b')

    def __init__(self, seed: int | None = None):
        """
        :param seed: 随机种子，None 表示每次随机。固定种子用于可重复测试。
        """
        self._seed = seed if seed is not None else random.randint(0, 2 ** 31)
        self._rng = random.Random(self._seed)
        self._rename_map: dict[str, str] = {}
        logger.info(f"[Obfuscator] 初始化，种子={self._seed}")

    # ------------------------------------------------------------------ #
    #  公开接口
    # ------------------------------------------------------------------ #

    def obfuscate(self, source: str) -> str:
        """
        对 source 执行完整混淆流程，返回混淆后的代码字符串。

        流程：
          1. 插入伪造 import 语句
          2. 在函数体内插入垃圾代码块
          3. 对局部变量名随机重命名
          4. 将部分内部字符串字面值编码
        """
        logger.info("[Obfuscator] 开始混淆...")

        # Step 1: 插入伪造 import 区块
        source = self._inject_fake_imports(source)

        # Step 2: 在函数体内插入垃圾代码块
        source = self._inject_junk_blocks(source)

        # Step 3: 局部变量重命名
        source = self._rename_locals(source)

        # Step 4: 对部分内部字符串编码（可选，保守模式）
        source = self._encode_internal_strings(source)

        logger.info("[Obfuscator] 混淆完成")
        return source

    # ------------------------------------------------------------------ #
    #  Step 1: 伪造 import
    # ------------------------------------------------------------------ #

    _FAKE_IMPORT_POOL = [
        "import hashlib as _hlib",
        "import struct as _stru",
        "import io as _io_mod",
        "import copy as _cp",
        "import itertools as _itl",
        "import functools as _ftl",
        "import platform as _plat",
        "import uuid as _uuid_mod",
        "import tempfile as _tmp_mod",
        "import weakref as _wrf",
    ]

    def _inject_fake_imports(self, source: str) -> str:
        """在 # === MERGED BUILD === 标记后面插入若干伪造 import。"""
        marker = "# === MERGED BUILD ==="
        if marker not in source:
            return source

        chosen = self._rng.sample(self._FAKE_IMPORT_POOL,
                                  k=self._rng.randint(3, 6))
        fake_block = '\n'.join(chosen) + '\n'

        # 插入到 marker 行之后
        source = source.replace(marker,
                                marker + '\n' + fake_block, 1)
        return source

    # ------------------------------------------------------------------ #
    #  Step 2: 垃圾代码块注入
    # ------------------------------------------------------------------ #

    def _inject_junk_blocks(self, source: str) -> str:
        """
        在每个 def 函数定义的第一行代码之后插入一个 if False: 死代码块。
        每个注入点使用不同的 seed 保证代码多样性。
        """
        lines = source.split('\n')
        result = []
        junk_counter = 0

        i = 0
        while i < len(lines):
            line = lines[i]
            result.append(line)

            # 检测函数定义行
            stripped = line.strip()
            if stripped.startswith('def ') and stripped.endswith(':'):
                indent = len(line) - len(line.lstrip())
                body_indent = indent + 4

                # 找到函数体第一行（跳过 docstring）
                j = i + 1
                while j < len(lines) and (lines[j].strip() == '' or
                                           lines[j].strip().startswith('"""') or
                                           lines[j].strip().startswith("'''")):
                    result.append(lines[j])
                    j += 1
                    # 跳过完整 docstring
                    if j < len(lines):
                        doc_line = lines[j - 1].strip()
                        quote = None
                        if doc_line.startswith('"""'): quote = '"""'
                        elif doc_line.startswith("'''"): quote = "'''"
                        
                        if quote and doc_line.count(quote) < 2:
                            while j < len(lines) and quote not in lines[j]:
                                result.append(lines[j])
                                j += 1
                            if j < len(lines):
                                result.append(lines[j])
                                j += 1

                i = j
                # 注入垃圾块
                junk = _junk_block(indent=body_indent,
                                   seed=self._seed + junk_counter)
                result.append(junk)
                junk_counter += 1
                continue

            i += 1

        return '\n'.join(result)

    # ------------------------------------------------------------------ #
    #  Step 3: 局部变量重命名
    # ------------------------------------------------------------------ #

    # 仅重命名以单个小写字母开头、长度 3-12 的非保护名称
    _RENAME_CANDIDATES = re.compile(r'\b([a-z][a-z_0-9]{2,11})\b')

    def _rename_locals(self, source: str) -> str:
        """
        统计源码中出现频率高的局部变量名，对非保护名称进行统一随机替换。
        只替换出现在赋值/参数位置的名称（保守策略，避免破坏属性访问）。
        """
        # 收集候选名称（出现次数 >= 2 且不在保护列表中）
        counts: dict[str, int] = {}
        for m in self._RENAME_CANDIDATES.finditer(source):
            name = m.group(1)
            if name not in self.PROTECTED_NAMES:
                counts[name] = counts.get(name, 0) + 1

        # 选取出现次数 2-20 次之间的名称（过多的可能是关键词，过少的没有意义）
        candidates = [n for n, c in counts.items() if 2 <= c <= 20]

        # 为每个候选生成唯一的混淆名称
        used_names: set[str] = set()
        for name in candidates:
            # 用 name+seed 的 hash 作为确定性随机
            digest = hashlib.md5(f"{name}{self._seed}".encode()).hexdigest()[:6]
            new_name = f"_{digest}"
            if new_name not in used_names:
                self._rename_map[name] = new_name
                used_names.add(new_name)

        if not self._rename_map:
            return source

        # 用 word-boundary 替换（避免替换子串）
        def replacer(m: re.Match) -> str:
            word = m.group(0)
            return self._rename_map.get(word, word)

        pattern = re.compile(
            r'\b(' + '|'.join(re.escape(k) for k in self._rename_map) + r')\b'
        )
        source = pattern.sub(replacer, source)
        logger.info(f"[Obfuscator] 重命名了 {len(self._rename_map)} 个局部变量名")
        return source

    # ------------------------------------------------------------------ #
    #  Step 4: 内部字符串编码
    # ------------------------------------------------------------------ #

    # 匹配非空的短字符串字面值（长度 4-40，避免编码超长字符串导致代码膨胀）
    _SHORT_STR_PATTERN = re.compile(r'"([A-Za-z][A-Za-z0-9_\-\.]{3,39})"')

    def _encode_internal_strings(self, source: str) -> str:
        """
        对部分简单的 ASCII 字符串字面值进行 bytes.decode() 编码。
        只替换匹配 _SHORT_STR_PATTERN 的字符串，且以随机概率决定是否替换（保守模式）。
        """
        def maybe_encode(m: re.Match) -> str:
            s = m.group(1)
            # 30% 概率替换，保持代码可读性，避免过度膨胀
            if self._rng.random() < 0.30:
                return _encode_string(s)
            return m.group(0)

        result = self._SHORT_STR_PATTERN.sub(maybe_encode, source)
        return result


# ======================================================================= #
#  便捷函数
# ======================================================================= #

def obfuscate_code(source: str, seed: int | None = None) -> str:
    """
    对源代码进行一次性混淆，返回混淆后的代码。

    :param source: 原始 Python 源代码字符串
    :param seed:   随机种子（可选）
    :return:       混淆后的 Python 源代码字符串
    """
    obfuscator = CodeObfuscator(seed=seed)
    return obfuscator.obfuscate(source)
