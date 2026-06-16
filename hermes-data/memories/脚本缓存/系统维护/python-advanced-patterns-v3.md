# Python 高级脚本模式（第三轮）— tqdm / Rich 源码精炼

## 1️⃣ tqdm (31k⭐, 1,524 行 std.py)

### 模式 12: 线程安全 + 多进程锁
```python
class TqdmDefaultWriteLock:
    th_lock = threading.RLock()   # 线程锁
    mp_lock = multiprocessing.RLock()  # 多进程锁

    def acquire(self, *a, **k):
        for lock in self.locks:
            lock.acquire(*a, **k)
    def release(self):
        for lock in self.locks[::-1]:  # 倒序释放
            lock.release()
```
**实战：** 看门狗多进程写 SQLite 时保证不冲突

### 模式 13: 智能更新节流
```python
def __iter__(self):
    # 变量内联（速度优化）
    mininterval = self.mininterval
    last_print_t = self.last_print_t
    n = self.n

    for obj in iterable:
        yield obj
        n += 1
        if n - last_print_n >= self.miniters:
            cur_t = time()
            if cur_t - last_print_t >= mininterval:
                self.update(...)  # 只有够了时间才更新
```
**实战：** 看门狗循环等待 Gateway 恢复时，不需要每 3 秒都读文件，用节流

### 模式 14: Bar 格式化类
```python
class Bar:
    """`str.format`-able 进度条 — 支持 [width][type] 格式"""
    ASCII = " 123456789#"
    UTF = " " + ''.join(chr(0x258F - i) for i in range(8))
    COLOUR_RESET = '\x1b[0m'

    def __init__(self, frac, default_len=10, charset=UTF):
        if not 0 <= frac <= 1:
            warn("clamping frac to range [0, 1]")
```
**实战：** 命令行工具的状态条

### 模式 15: 格式化工具函数
```python
@staticmethod
def format_sizeof(num, suffix='', divisor=1000):
    """1.2k, 3.4M, 5.6G — SI 前缀"""
    for unit in ['', 'k', 'M', 'G', 'T', 'P', 'E', 'Z']:
        if abs(num) < 999.5:
            if abs(num) < 9.995: return f'{num:1.2f}{unit}{suffix}'
            if abs(num) < 99.95: return f'{num:2.1f}{unit}{suffix}'
            return f'{num:3.0f}{unit}{suffix}'
        num /= divisor
    return f'{num:3.1f}Y{suffix}'

@staticmethod
def format_interval(t):
    """秒数 → [H:]MM:SS"""
    sign = '-' if t < 0 else ''
    mins, s = divmod(abs(int(t)), 60)
    h, m = divmod(mins, 60)
    return f'{sign}{h}:{m:02d}:{s:02d}' if h else f'{sign}{m:02d}:{s:02d}'
```

---

## 2️⃣ Rich (56k⭐, 2,684 行 console.py)

### 模式 16: Renderable 协议
```python
class RenderableType(Protocol):
    """任何实现了 __rich_console__ 的对象都可渲染"""
    def __rich_console__(
        self, console: Console, options: ConsoleOptions
    ) -> RenderResult: ...
```
**实战：** 看门狗报告可以做成 Renderable，任意拼接段落

### 模式 17: Console 作为中央编排器
```python
class Console:
    def __init__(self, color_system='auto', force_terminal=None, width=None):
        self._color_system = color_system
        self._width = width or shutil.get_terminal_size().columns

    def print(self, *objects, sep=' ', end='\n', style=None):
        renderables = self._convert_renderables(objects)
        for renderable in renderables:
            rendered = self.render(renderable, ...)
            # 写出到文件/终端/字符串
```
**实战：** 看门狗的输出可以有一个统一的 Console-like 编排器

### 模式 18: Live 实时刷新
```python
class Live:
    """动态更新显示内容"""
    def __init__(self, renderable, refresh_per_second=4):
        self._renderable = renderable
        self._refresh_per_second = refresh_per_second

    def __enter__(self):
        self.start()
        return self

    def update(self, renderable):
        self._renderable = renderable
        self.refresh()

    def refresh(self):
        # 用 ANSI 转义码原地刷新
        output = self._render()
        self._console.file.write(output)
```
**实战：** 客户发送管道的实时进度显示

---

## 应用到小马管道的升级

| 模式 | 应用到 | 效果 |
|:-----|:-------|:-----|
| 模式 12: 锁管理 | SQLite JobStore | 多进程写不冲突 |
| 模式 13: 节流 | Gateway 等待循环 | 减少不必要的文件 IO |
| 模式 15: format_sizeof | 看门狗报告 | 文件大小/网络速率的友好显示 |
| 模式 17: 编排器 | 多 Agent 报告输出 | 统一的消息格式 |
| 模式 18: Live | 发送管道进度 | 实时看到发送到第几个客户 |
