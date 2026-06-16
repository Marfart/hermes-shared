#!/usr/bin/env python3
"""
QP/C Active Object + Hierarchical State Machine 概念演示 (Python移植版)

学习自: QuantumLeaps/qpc — 专为ARM Cortex-M设计的实时事件框架
原始项目: https://github.com/QuantumLeaps/qpc (8.1.4, ~2.5k⭐)

核心设计模式:
1. Active Object (Actor) 模型 — 异步事件驱动并发
2. 层次状态机 (HSM) — UML状态图实现
3. 事件队列 + 内存池 — 零碎片动态事件分配
"""

from enum import IntEnum
from dataclasses import dataclass, field
from typing import Optional, Callable, List
import time


# ================================================================
# 第1层：事件系统 (QEvt)
# ================================================================
class Signal(IntEnum):
    """QP/C保留信号"""
    EMPTY = 0   # 查询父状态
    ENTRY = 1   # 进入状态
    EXIT = 2    # 退出状态
    INIT = 3    # 初始转换
    USER = 4    # 用户信号起始


@dataclass
class QEvt:
    """QP/C事件 — 8字节对齐设计"""
    sig: int
    pool_num: int = 0   # 0=静态事件
    ref_ctr: int = 0    # 引用计数


# ================================================================
# 第2层：层次状态机引擎 (QEP)
# ================================================================
class Return(IntEnum):
    """状态处理函数返回值"""
    SUPER = 0       # 委托给父状态
    UNHANDLED = 1   # 未处理（守卫条件失败）
    HANDLED = 2     # 已处理
    TRAN = 3        # 状态转换
    IGNORED = 5     # 忽略事件


class QHsm:
    """层次状态机基类 (QP/C的QHsm)"""
    
    def __init__(self, owner, initial: Callable):
        self.owner = owner      # 拥有此HSM的对象
        self.state = initial    # 当前活动状态
        self.temp = initial     # 临时存储（转换目标/父状态）
    
    def init(self):
        """执行顶层初始转换 (QP/C的QHsm_init_)"""
        path = []
        self.temp = self.state
        
        # 执行初始转换
        r = self.temp(self.owner, None)
        assert r == Return.TRAN, "初始转换必须返回TRAN"
        
        # 构建入口路径
        while True:
            path.append(self.temp)
            # 查询父状态 — 当返回None时表示到达顶层
            self.temp(self.owner, None)
            if self.temp == self.state or self.temp is None:
                break
        
        # 执行入口动作（从LCA到目标）
        for s in reversed(path):
            s(self.owner, QEvt(Signal.ENTRY))
        
        self.state = path[0]
    
    def dispatch(self, e: QEvt):
        """事件分发 — 层次遍历状态树 (QP/C的QHsm_dispatch_)"""
        path = [None] * 8
        ip = 8
        s = self.state
        
        self.temp = s
        
        # 自底向上尝试处理事件
        while True:
            s = self.temp
            ip -= 1
            path[ip] = s
            r = s(self.owner, e)
            
            if r == Return.UNHANDLED:
                # 守卫条件失败 → 查询父状态
                r = s(self.owner, None)  # 用None查询父状态
            
            if r == Return.SUPER:
                # self.temp已设置为父状态，继续向上
                if self.temp is None:
                    r = Return.IGNORED  # 到达顶层 → 忽略事件
                    break
                continue
            
            break
        
        if r == Return.TRAN:
            # 执行状态转换
            # 1. 退出当前状态到转换源
            for i in range(7, ip, -1):
                path[i](self.owner, QEvt(Signal.EXIT))
            
            # 2. 进入目标状态
            path[0] = self.temp
            ip = 1
            self.temp = path[0]
            if self.temp is not None:
                self.temp(self.owner, None)  # 查询父状态
            
            while self.temp is not None and self.temp != s and ip < 8:
                path[ip] = self.temp
                ip += 1
                if self.temp is not None:
                    self.temp(self.owner, None)
            
            for i in range(ip - 1, -1, -1):
                path[i](self.owner, QEvt(Signal.ENTRY))
            
            self.state = path[0]


# ================================================================
# 第3层：Active Object框架 (QF)
# ================================================================
class EventQueue:
    """环形缓冲区事件队列 (QP/C的QEQueue)"""
    
    def __init__(self, size: int = 16):
        self.ring = [None] * size
        self.head = 0
        self.tail = 0
        self.count = 0
        self.size = size
    
    def post(self, e: QEvt) -> bool:
        if self.count >= self.size:
            return False
        self.ring[self.head] = e
        self.head = (self.head + 1) % self.size
        self.count += 1
        return True
    
    def get(self) -> Optional[QEvt]:
        if self.count == 0:
            return None
        e = self.ring[self.tail]
        self.tail = (self.tail + 1) % self.size
        self.count -= 1
        return e


class MemoryPool:
    """固定大小内存池 (QP/C的QMPool) — 零碎片分配"""
    
    def __init__(self, block_size: int, num_blocks: int):
        self.block_size = block_size
        self.n_free = num_blocks
        self.n_min = num_blocks
        self.pool = [None] * num_blocks
    
    def get(self) -> Optional[bytearray]:
        if self.n_free == 0:
            return None
        idx = self.n_free - 1
        block = bytearray(self.block_size)
        self.pool[idx] = block
        self.n_free -= 1
        if self.n_free < self.n_min:
            self.n_min = self.n_free
        return block
    
    def put(self, block: bytearray):
        self.n_free += 1


class QActive:
    """Active Object基类 (QP/C的QActive)"""
    
    def __init__(self, initial: Callable, prio: int = 1):
        self.hsm = QHsm(self, initial)
        self.prio = prio
        self.queue = EventQueue()
    
    def start(self):
        self.hsm.init()


class QFramework:
    """框架全局状态"""
    
    def __init__(self):
        self.active: List[QActive] = []
    
    def add(self, ao: QActive):
        self.active.append(ao)
    
    def publish(self, e: QEvt):
        """发布事件到所有AO"""
        for ao in self.active:
            ao.queue.post(e)
    
    def run(self, cycles: int = 5):
        """主循环"""
        print(f"[QF] 框架启动，{len(self.active)}个Active Object\n")
        
        for cycle in range(cycles):
            print(f"--- 周期 {cycle + 1} ---")
            
            # 发送TICK事件
            self.publish(QEvt(Signal.USER, 0, 0))
            
            # 处理每个AO的事件队列
            for ao in self.active:
                while True:
                    e = ao.queue.get()
                    if e is None:
                        break
                    print(f"  [AO#{ao.prio}] 处理事件 sig={e.sig}")
                    ao.hsm.dispatch(e)


# ================================================================
# 示例：LED控制器 — 层次状态机演示
# ================================================================
class LedController(QActive):
    """LED控制器 — 演示层次状态机"""
    
    # 用户信号
    SIG_BUTTON_PRESS = Signal.USER
    SIG_BUTTON_DOUBLE = Signal.USER + 1
    SIG_TIMEOUT = Signal.USER + 2
    SIG_TICK = Signal.USER + 3
    
    def __init__(self):
        super().__init__(self._initial, prio=1)
        self.brightness = 0
        self.blink_count = 0
    
    # --- 状态处理函数 ---
    
    def _initial(self, me, e):
        """顶层初始转换"""
        print("[LED] 初始化 → Off状态")
        self.hsm.temp = self._off  # Q_TRAN(LedController_off)
        return Return.TRAN
    
    def _off(self, me, e):
        """Off状态"""
        if e is None:
            self.hsm.temp = self._on  # 父状态是on
            return Return.SUPER
        
        if e.sig == Signal.ENTRY:
            print("  [LED-Off] 进入 — LED熄灭")
            self.brightness = 0
            return Return.HANDLED
        
        elif e.sig == Signal.EXIT:
            print("  [LED-Off] 退出")
            return Return.HANDLED
        
        elif e.sig == self.SIG_BUTTON_PRESS:
            print("  [LED-Off] 按钮按下 → 切换到On")
            self.hsm.temp = self._on
            return Return.TRAN
        
        return Return.UNHANDLED
    
    def _on(self, me, e):
        """On状态"""
        if e is None:
            self.hsm.temp = None  # 顶层状态
            return Return.SUPER
        
        if e.sig == Signal.ENTRY:
            print(f"  [LED-On] 进入 — LED亮起 (亮度={self.brightness})")
            return Return.HANDLED
        
        elif e.sig == Signal.EXIT:
            print("  [LED-On] 退出")
            return Return.HANDLED
        
        elif e.sig == self.SIG_BUTTON_PRESS:
            print("  [LED-On] 按钮按下 → 切换到Off")
            self.hsm.temp = self._off
            return Return.TRAN
        
        elif e.sig == self.SIG_BUTTON_DOUBLE:
            print("  [LED-On] 双击 → 进入Blinking模式")
            self.blink_count = 3
            self.hsm.temp = self._blinking
            return Return.TRAN
        
        return Return.UNHANDLED
    
    def _blinking(self, me, e):
        """Blinking状态 (On的子状态)"""
        if e is None:
            self.hsm.temp = self._on  # 父状态是on
            return Return.SUPER
        
        if e.sig == Signal.ENTRY:
            print(f"  [LED-Blink] 进入 — 开始闪烁 ({self.blink_count}次)")
            return Return.HANDLED
        
        elif e.sig == Signal.EXIT:
            print("  [LED-Blink] 退出")
            return Return.HANDLED
        
        elif e.sig == self.SIG_TICK:
            self.blink_count -= 1
            print(f"  [LED-Blink] 闪烁! 剩余={self.blink_count}")
            if self.blink_count == 0:
                print("  [LED-Blink] 闪烁结束 → 回到On")
                self.hsm.temp = self._on
                return Return.TRAN
            return Return.HANDLED
        
        return Return.UNHANDLED


# ================================================================
# 主函数
# ================================================================
def main():
    print("=" * 50)
    print(" QP/C Active Object + HSM 概念演示 (Python)")
    print(" 学习自: QuantumLeaps/qpc (ARM Cortex-M RTEF)")
    print("=" * 50)
    
    # 创建框架
    qf = QFramework()
    
    # 创建LED控制器
    led = LedController()
    
    # 初始化HSM
    led.start()
    
    # 注册到框架
    qf.add(led)
    
    # 运行框架
    qf.run(cycles=5)
    
    print("\n" + "=" * 50)
    print(" 演示结束")
    print("=" * 50)


if __name__ == "__main__":
    main()
