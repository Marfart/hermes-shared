# MicroPython 全流程贯通参考 (21.7k⭐)

## 覆盖的源文件

| 文件 | 功能 | 核心理解 |
|------|------|---------|
| py/obj.h | 对象模型 | 标记指针系统: Repr A(32bit)/C(64bit NaN-boxing) |
| py/gc.c | 内存管理 | 三色标记-清扫GC，没有free list！全扫描ATB |
| py/vm.c | 虚拟机执行 | 值栈从低到高增长（为了Python从左到右求值语义） |
| py/runtime.c | 运行时 | nlr_setjmp异常机制、模块初始化 |
| py/compile.c | 编译器 | 跳过AST的CST→字节码单遍编译 |
| py/lexer.c | 词法分析 | 3字符前瞻(chr0/chr1/chr2)、缩进栈、tok_enc编码 |
| py/parse.c | 解析器 | 语法表驱动递归下降、大块分配器(无碎片) |
| py/grammar.h | 语法规则 | 130+ DEF_RULE宏、or/and/list三种动作 |
| py/emitbc.c | 字节码发射 | label回填、可变长DECODE_UINT编码 |
| py/bc.h | 字节码格式 | header(2+2bytes) + code + const |

## 5 大核心设计

### 1. 标记指针 (Tagged Pointer)

| Repr | 架构 | 编码方式 |
|------|------|---------|
| A | ARM 32-bit | bit0=1→small int, bit0=0+bit1=1→QSTR, 00→ptr |
| B | x86 32-bit | 同A但少1bit整数空间 |
| C | x86-64 | NaN-boxing: float用IEEE754 64bit, 非float用0x7fff前缀 |
| D | ARM 64-bit | 48位地址+16位tag |

检测顺序很重要：
```
if obj & 1:  → small_int  ✅先检查这个
elif obj & 2: → QSTR
else:         → 指针
```

### 2. GC 无 free list

跟 CPython 完全不同：
- 没有 `free_list` 链表
- gc_sweep() 直接扫描 ATB 位图找连续 FREE 块
- 节省了 free list 的内存（在 16KB MCU 上每字节都贵）
- GC 实现仅 ~300 行 C 代码

三种位图:
- ATB (Allocation Table Block): 0=free, 1=head, 2=tail
- MB (Mark Block): 标记阶段用
- FB (Finalisation Block): 是否需要析构

### 3. 值栈增长方向

跟 C 栈相反！C 栈向下增长，MicroPython 值栈向上增长。
原因: Python 语义要求**参数从左到右求值**。
值栈向上增长保证参数在栈中的自然顺序。

### 4. 字节码可变长编码 (DECODE_UINT)

```
#define DECODE_UINT { \
    unum = 0; \
    do { \
        unum = (unum << 7) + (*ip & 0x7f); \
    } while ((*ip++ & 0x80) != 0); \
}
```

高位bit标记续段。常见指令 1 字节，偶尔 2 字节。
比 CPython 固定 32bit 省 3-5 倍。

### 5. 无yacc/bison的解析器

没有用 bison/yacc 生成 parser!
90+ 条语法产生式全部手写递归下降 (parse.c)。
跳过 AST 直接 CST→字节码 (compile.c)。
内存: 每个 parse node 只占 4-8 字节（CPython 的 AST node 要 40+）。

## Lexer 细节 (lexer.c)

- 3字符前瞻窗口: chr0/chr1/chr2 通过 next_char() 滚动
- 缩进栈: indent_level[] 数组, indent_push/pop 管理
- tok_enc: 操作符编码表 (如 "<e=c<e=" → <,<<,<<=,< =)
- 输入来源: reader.readbyte() 可文件/字符串/REPL
- CR/LF/CRLF 统一成 LF
- 文件末自动插入 NEWLINE（如果最后一行没有）

## Parser 细节 (parse.c)

- 语法规则编译时展开为 3 张表: rule_act_table, rule_arg_combined_table, rule_arg_offset_table
- 运行时: 规则栈 (rule_stack) + 结果栈 (result_stack)
- 大块分配器 mp_parse_chunk_t: 连续内存 ~512字节/块, m_renew_maybe 优先扩展现有块
- 递归函数: parse_rule() → 匹配语法 → push_result_rule() → 继续

## 完整流程: print("hello")

```
Source → Lexer → Token Stream → Parser(CST) → Compiler(CST→Bytecode) → VM

词法分析: 
  "print"  → NAME(print)
  "("      → DEL_PAREN_OPEN
  "\"hello\"" → STRING("hello")
  ")"      → DEL_PAREN_CLOSE
  "\n"     → NEWLINE
  EOF      → END

编译:
  compile_file_input()
  → compile_stmt() → compile_simple_stmt() → compile_expr_stmt()
  → compile_atom_power_trailer()
    → compile_atom("print")    → LOAD_NAME print
    → compile_trailer_paren()  
      → compile_atom("hello")  → LOAD_CONST "hello"
    → CALL_FUNCTION n=1
  → POP_TOP → LOAD_CONST None → RETURN_VALUE

字节码:
  LOAD_NAME       0 (print)
  LOAD_CONST      0 ('hello')
  CALL_FUNCTION   1
  POP_TOP
  LOAD_CONST      1 (None)
  RETURN_VALUE
```

## 验证脚本
memories/脚本缓存/理解验证/trace_print_hello.py — 全流程微型实现
memories/脚本缓存/理解验证/test_tagged_pointers.py — 标记指针/GC/值栈模拟