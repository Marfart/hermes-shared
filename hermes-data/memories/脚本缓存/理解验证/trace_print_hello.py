"""
==========================================================
MicroPython 全流程贯通 — 从 print("hello") 到 VM 执行
==========================================================

追踪路径: Source → Lexer → Parser(CST) → Compiler → Emitter → Bytecode → VM

参考: 源码 py/{lexer,parse,compile,emitbc,vm,runtime}.c + obj.h + gc.c
"""

# ============================================================
# STAGE 1: LEXER 词法分析
# ============================================================
# 源码: py/lexer.c
# 核心机制:
#   - 3字符前瞻窗口: chr0/chr1/chr2 (next_char() 滚动)
#   - 缩进栈: indent_level[] (push/pop 管理 INDENT/DEDENT)
#   - 特殊编码表: tok_enc 把操作符编码成字符串匹配表
#   - 输入来源: reader.readbyte() (可以是文件/字符串/REPL)
#   - CR/LF/CRLF 统一成 LF


# ============================================================
# STAGE 2: PARSER 解析 (递归下降 + 语法表驱动)
# ============================================================
# 源码: py/parse.c + py/grammar.h
# 核心机制:
#   - 语法规则编码在 grammar.h 的 DEF_RULE/DEF_RULE_NC 宏中
#   - parse.c 编译时展开生成3张表: rule_act_table, rule_arg_combined_table, rule_arg_offset_table
#   - 运行时: 规则栈 (rule_stack) + 结果栈 (result_stack)
#   - 不生成 AST! 直接生成 CST (具体语法树) 给编译器


# ============================================================
# STAGE 3: COMPILER 编译 (compile.c → CST → bytecode)
# ============================================================
# 源码: py/compile.c
# 核心机制:
#   - compile_t 结构体: 编译状态 (scope_cur, emit_method_table, ...)
#   - 编译函数表: compile_function_table[RULE_xxx]
#   - 每个 grammar 规则对应一个编译函数


# ============================================================
# STAGE 4: EMITTER (emitbc.c → 字节码输出)
# ============================================================
# 源码: py/emitbc.c + py/bc.h
# 核心机制:
#   - emit_t 结构体 (emit_method_table 指向 emitbc 的函数)
#   - 字节码缓冲区: bytecode_array, const_table, cell_table
#   - 预计算跳转偏移 (label 回填)
#   - 字节码编码: DECODE_UINT 宏 (可变长: 高位 bit 标记续段)


# ================================================================
# 从零写微型 MicroPython 执行引擎 (Python 实现)
# 证明: 我真的理解了 lexer/parser/compiler/emitter/vm 的全流程
# ================================================================

class Token:
    """词法单元 — lexer 产出"""
    NAME = 'NAME'
    NUMBER = 'NUMBER'
    STRING = 'STRING'
    NEWLINE = 'NEWLINE'
    INDENT = 'INDENT'
    DEDENT = 'DEDENT'
    KEYWORD = 'KEYWORD'
    OP = 'OP'
    END = 'END'

    def __init__(self, kind, value=None, line=0, col=0):
        self.kind = kind
        self.value = value
        self.line = line
        self.col = col

    def __repr__(self):
        return f"Token({self.kind}, {self.value!r})"


class Lexer_MP:
    """
    MicroPython 风格词法分析器
    设计灵感: lexer.c 的3字符前瞻 + tok_enc 编码表 + 缩进栈
    """
    KEYWORDS = {
        'if', 'else', 'elif', 'while', 'for', 'def',
        'return', 'True', 'False', 'None', 'and', 'or', 'not',
        'in', 'is', 'import', 'from', 'class', 'try', 'except',
        'finally', 'with', 'as', 'raise', 'break', 'continue',
        'pass', 'lambda', 'yield', 'global', 'nonlocal',
        'del', 'assert', 'async', 'await',
    }

    def __init__(self, text):
        self.text = text
        self.pos = 0
        self.line = 1
        self.col = 1
        # 缩进栈 — from lexer.c indent_level[]
        self.indent_stack = [0]
        self.pending = []
        self._tokenize()

    def _tokenize(self):
        """从源码产出一个token列表 (lexer.c 的 main loop)"""
        tokens = []
        lines = self.text.splitlines(True)

        for line_idx, raw_line in enumerate(lines):
            line_num = line_idx + 1
            # 计算缩进 — 类似 lexer.c 调用 indent_push/pop
            indent = 0
            for ch in raw_line:
                if ch == ' ':
                    indent += 1
                elif ch == '\t':
                    indent = ((indent // 8) + 1) * 8  # TAB_SIZE = 8
                elif ch == '\n':
                    indent = 0
                    break
                else:
                    break

            # 空行/注释行 → 跳过 (lexer.c: 遇到空白行不产生 NEWLINE)
            stripped = raw_line.strip()
            if not stripped or stripped.startswith('#'):
                continue

            # 缩进变化 → 产生 INDENT/DEDENT (lexer.c: indent_push/pop)
            top = self.indent_stack[-1]
            if indent > top:
                self.indent_stack.append(indent)
                tokens.append(Token(Token.INDENT, line=line_num))
            elif indent < top:
                while self.indent_stack and self.indent_stack[-1] > indent:
                    self.indent_stack.pop()
                    tokens.append(Token(Token.DEDENT, line=line_num))
                if self.indent_stack[-1] != indent:
                    raise SyntaxError(
                        f"缩进不匹配: 期望 {self.indent_stack[-1]}, 实际 {indent}"
                    )

            # 词法分析: 逐字符
            pos = 0
            while pos < len(stripped):
                ch = stripped[pos]

                # 跳过空白 (lexer.c: is_whitespace → next_char)
                if ch in ' \t':
                    pos += 1
                    continue

                # 注释跳过 (lexer.c: is_char('#') → 跳过整行)
                if ch == '#':
                    break

                # 字符串 (lexer.c: is_string_or_bytes() → 有8种前缀组合)
                if ch in '"\'':
                    quote = ch
                    j = pos + 1
                    s = []
                    while j < len(stripped) and stripped[j] != quote:
                        if stripped[j] == '\\' and j + 1 < len(stripped):
                            esc_map = {
                                'n': '\n', 't': '\t', 'r': '\r',
                                '\\': '\\', '"': '"', "'": "'"
                            }
                            s.append(esc_map.get(stripped[j+1], stripped[j+1]))
                            j += 2
                        else:
                            s.append(stripped[j])
                            j += 1
                    if j >= len(stripped):
                        raise SyntaxError(f"字符串未闭合 at line {line_num}")
                    tokens.append(Token(Token.STRING, ''.join(s), line_num))
                    pos = j + 1
                    continue

                # 标识符/关键词 (lexer.c: is_head_of_identifier/is_tail_of_identifier)
                if ch.isalpha() or ch == '_':
                    j = pos
                    while j < len(stripped) and (stripped[j].isalnum() or stripped[j] == '_'):
                        j += 1
                    word = stripped[pos:j]
                    if word in self.KEYWORDS:
                        tokens.append(Token(Token.KEYWORD, word, line_num))
                    else:
                        tokens.append(Token(Token.NAME, word, line_num))
                    pos = j
                    continue

                # 数字
                if ch.isdigit() or (ch == '.' and pos+1 < len(stripped) and stripped[pos+1].isdigit()):
                    j = pos
                    hex_mode = False
                    if ch == '0' and pos+1 < len(stripped) and stripped[pos+1] in 'xX':
                        j = pos + 2
                        while j < len(stripped) and (stripped[j] in '0123456789abcdefABCDEF'):
                            j += 1
                        val = int(stripped[pos:j], 16)
                        tokens.append(Token(Token.NUMBER, val, line_num))
                        pos = j
                        continue
                    while j < len(stripped) and (stripped[j].isdigit() or stripped[j] == '.'):
                        j += 1
                    num_str = stripped[pos:j]
                    if num_str.count('.') > 1:
                        raise SyntaxError(f"无效数字 {num_str}")
                    val = int(num_str) if '.' not in num_str else float(num_str)
                    tokens.append(Token(Token.NUMBER, val, line_num))
                    pos = j
                    continue

                # 操作符/分隔符
                # 灵感: lexer.c 的 tok_enc 编码表 (操作符编码成字符串)
                ops = {
                    '(': 'LPAREN', ')': 'RPAREN',
                    ',': 'COMMA', ':': 'COLON',
                    '=': 'ASSIGN', '+': 'PLUS', '-': 'MINUS',
                    '*': 'STAR', '/': 'SLASH', '%': 'MOD',
                    '==': 'EQ', '!=': 'NE', '<': 'LT',
                    '>': 'GT', '<=': 'LE', '>=': 'GE',
                    '**': 'POW', '//': 'FLOORDIV',
                }
                # 双字符优先 (tok_enc 的 "e<c<e=" 多字符匹配)
                if pos + 1 < len(stripped) and stripped[pos:pos+2] in ops:
                    tokens.append(Token(Token.OP, ops[stripped[pos:pos+2]], line_num))
                    pos += 2
                elif ch in {k[0] for k in ops}:
                    tokens.append(Token(Token.OP, ops[ch], line_num))
                    pos += 1
                else:
                    raise SyntaxError(f"未知字符 {ch!r} at line {line_num}")

            tokens.append(Token(Token.NEWLINE, line=line_num))

        # 文件末尾回退缩进 (lexer.c: 遇到 END 前 pop 所有 INDENT)
        while len(self.indent_stack) > 1:
            self.indent_stack.pop()
            tokens.append(Token(Token.DEDENT, line=len(lines)))

        tokens.append(Token(Token.END, line=len(lines)))
        self.pending = tokens


class TinyMicroPython:
    """
    微型 MicroPython: 最小可运行的解释器
    完整管道: Lexer → Parser/Compiler → Bytecode → VM
    跳过了 AST (跟 real MicroPython 一样的内存优化)
    """

    def __init__(self):
        self.vm = None

    def compile(self, text):
        """lex → parse → compile 一步到位 (single-pass, 同 compile.c)"""
        lexer = Lexer_MP(text)
        self.tokens = lexer.pending
        self.token_pos = 0

        bytecode = []
        const_pool = []
        name_pool = []

        self._expr_stmt(bytecode, const_pool, name_pool)

        return bytecode, const_pool, name_pool

    def _peek(self):
        if self.token_pos < len(self.tokens):
            return self.tokens[self.token_pos]
        return Token(Token.END)

    def _eat(self):
        t = self.tokens[self.token_pos]
        self.token_pos += 1
        return t

    def _expect(self, kind, value=None):
        t = self._eat()
        if t.kind != kind or (value is not None and t.value != value):
            raise SyntaxError(f"期望 {kind}({value}), 实际 {t}")
        return t

    def _expr_stmt(self, bc, cp, np):
        """表达式语句: 对应 compile_expr_stmt()"""

        # 先检查是不是赋值 (x = expr)
        # 看当前token是不是 NAME, 下一个 token 是不是 '='
        t = self._peek()
        if t.kind == Token.NAME and self.token_pos + 1 < len(self.tokens) and \
           self.tokens[self.token_pos + 1].kind == Token.OP and \
           self.tokens[self.token_pos + 1].value == 'ASSIGN':
            # 赋值路径: 不 LOAD 左值!
            name_token = self._eat()  # NAME
            self._expect(Token.OP, 'ASSIGN')  # '='
            self._power(bc, cp, np)  # 右值
            if name_token.value not in np:
                np.append(name_token.value)
            bc.append(('STORE_NAME', np.index(name_token.value)))
        else:
            # 表达式语句 (函数调用)
            self._power(bc, cp, np)
            bc.append(('POP_TOP',))

    def _power(self, bc, cp, np):
        """power: atom trailer* — 对应 compile_atom_power_trailer()"""
        self._atom(bc, cp, np)

        while self._peek().kind == Token.OP and self._peek().value == 'LPAREN':
            self._eat()  # '('
            nargs = 0
            if not (self._peek().kind == Token.OP and self._peek().value == 'RPAREN'):
                nargs = self._arglist(bc, cp, np)
            self._expect(Token.OP, 'RPAREN')
            bc.append(('CALL_FUNCTION', nargs))

    def _atom(self, bc, cp, np):
        """atom: 基本单元 — 对应 compile_atom()"""
        t = self._eat()
        if t.kind == Token.NAME:
            if t.value not in np:
                np.append(t.value)
            bc.append(('LOAD_NAME', np.index(t.value)))
        elif t.kind == Token.NUMBER:
            cp.append(t.value)
            bc.append(('LOAD_CONST', len(cp) - 1))
        elif t.kind == Token.STRING:
            cp.append(t.value)
            bc.append(('LOAD_CONST', len(cp) - 1))
        elif t.kind == Token.KEYWORD:
            if t.value == 'True':
                cp.append(True)
                bc.append(('LOAD_CONST', len(cp) - 1))
            elif t.value == 'False':
                cp.append(False)
                bc.append(('LOAD_CONST', len(cp) - 1))
            elif t.value == 'None':
                cp.append(None)
                bc.append(('LOAD_CONST', len(cp) - 1))

    def _arglist(self, bc, cp, np):
        """参数列表 — 对应 compile_arglist()"""
        nargs = 0
        while True:
            self._power(bc, cp, np)
            nargs += 1
            if self._peek().kind == Token.OP and self._peek().value == ',':
                self._eat()
            else:
                break
        return nargs

    def run(self, text):
        """完整管道: lex → compile → vm execute"""
        bc, cp, np = self.compile(text)

        print(f"  [词法分析] tokens: {len(self.tokens)} 个")
        print(f"  [字节码] {len(bc)} 条指令")
        print(f"  [常量池] {cp}")
        print(f"  [名称表] {np}")
        print(f"  [字节码列表]")
        for i, instr in enumerate(bc):
            parts = [f"    {i}: {instr[0]}"]
            if len(instr) > 1:
                detail = instr[1]
                if instr[0] == 'LOAD_CONST':
                    parts.append(f" {cp[detail]!r}")
                elif instr[0] == 'LOAD_NAME':
                    parts.append(f" {np[detail]}")
                else:
                    parts.append(f" {detail}")
            print(''.join(parts))

        # VM 执行 (模拟 vm.c 的 dispatch_loop)
        value_stack = []
        ip = 0

        builtins = {
            'print': lambda *args: print(f"    → print({', '.join(repr(a) for a in args)})"),
            'len': len,
            'range': range,
            'int': int,
            'str': str,
            'float': float,
            'type': type,
        }

        globals_dict = {}

        print(f"\n  [VM执行]")

        while ip < len(bc):
            instr = bc[ip]
            op = instr[0]

            if op == 'LOAD_CONST':
                value_stack.append(cp[instr[1]])
                ip += 1

            elif op == 'LOAD_NAME':
                name = np[instr[1]]
                if name in globals_dict:
                    value_stack.append(globals_dict[name])
                elif name in builtins:
                    value_stack.append(builtins[name])
                else:
                    raise NameError(f"name '{name}' is not defined")
                ip += 1

            elif op == 'CALL_FUNCTION':
                nargs = instr[1]
                args = []
                for _ in range(nargs):
                    args.insert(0, value_stack.pop())
                func = value_stack.pop()
                result = func(*args)
                value_stack.append(result)
                ip += 1

            elif op == 'POP_TOP':
                value_stack.pop()
                ip += 1

            elif op == 'STORE_NAME':
                name = np[instr[1]]
                val = value_stack.pop()
                globals_dict[name] = val
                ip += 1

            else:
                raise RuntimeError(f"未知指令: {op}")

        print(f"  [VM完成] 栈空={len(value_stack)==0}")
        return value_stack


# ================================================================
# 运行验证
# ================================================================

print("=" * 60)
print("MicroPython 全流程贯通验证")
print("从零实现: Lexer → Parser/Compiler → Bytecode → VM")
print("基于源码: py/{lexer,parse,compile,emitbc,vm,runtime}.c")
print("=" * 60)

print("\n" + "─" * 60)
print("测试1: print('hello')")
print("─" * 60)
tmp = TinyMicroPython()
tmp.run("print('hello')")

print("\n" + "─" * 60)
print("测试2: x = 42")
print("─" * 60)
tmp2 = TinyMicroPython()
tmp2.run("x = 42")

print("\n" + "─" * 60)
print("测试3: print(len('abc'))")
print("─" * 60)
tmp3 = TinyMicroPython()
tmp3.run("print(len('abc'))")

print("\n" + "─" * 60)
print("测试4: z = 3 + 4 (未来扩展: 二元运算)")
print("─" * 60)
# 目前只支持函数调用 + 赋值
# 展示了管道架构可扩展性

print("\n" + "=" * 60)
print("验证完成")
print("=" * 60)