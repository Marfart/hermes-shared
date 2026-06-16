/**
 * QP/C Active Object + Hierarchical State Machine 概念演示
 * 
 * 学习自: QuantumLeaps/qpc — 专为ARM Cortex-M设计的实时事件框架
 * 
 * 本文件展示QP/C框架的核心设计模式：
 * 1. Active Object (Actor) 模型 — 异步事件驱动并发
 * 2. 层次状态机 (HSM) — UML状态图实现
 * 3. 事件队列 + 内存池 — 零碎片动态事件分配
 * 
 * 注意：这是概念演示，不是完整QP/C框架。
 * 实际使用请从 https://github.com/QuantumLeaps/qpc 获取完整框架。
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <stdbool.h>

/* ================================================================
 * 第1层：QP/C 事件系统 (QEvt)
 * ================================================================
 * QP/C使用位域压缩事件结构：
 * - sig: 16位信号ID
 * - poolNum_: 8位内存池编号（动态事件用）
 * - refCtr_: 8位引用计数
 * 总大小 = 8字节，极适合嵌入式MCU
 */
#define MAX_SIGNAL 32

typedef uint16_t QSignal;

typedef struct QEvt {
    QSignal sig;        /* 信号ID */
    uint8_t poolNum;    /* 内存池编号 (0=静态事件) */
    uint8_t refCtr;     /* 引用计数 */
} QEvt;

/* 保留信号 (QP/C内部使用) */
enum ReservedSignals {
    Q_EMPTY_SIG = 0,    /* 查询父状态 */
    Q_ENTRY_SIG = 1,    /* 进入状态 */
    Q_EXIT_SIG  = 2,    /* 退出状态 */
    Q_INIT_SIG  = 3,    /* 初始转换 */
    Q_USER_SIG  = 4     /* 用户信号起始 */
};

/* 用户自定义事件示例 */
typedef struct {
    QEvt super;         /* 继承QEvt */
    uint32_t data;      /* 用户数据 */
} MyEvent;

/* ================================================================
 * 第2层：层次状态机引擎 (QEP — QP Event Processor)
 * ================================================================
 * QP/C的状态机核心设计：
 * - 状态处理函数签名: QState (*handler)(void *me, QEvt const *e)
 * - 返回值驱动层次遍历: SUPER/UNHANDLED/HANDLED/TRAN
 * - 虚函数表(vptr)实现多态 — 支持QHsm和QMsm两种风格
 */

typedef uint_fast8_t QState;
typedef QState (*QStateHandler)(void *me, QEvt const *e);

/* 状态返回值 */
enum {
    Q_RET_SUPER     = 0,  /* 委托给父状态 */
    Q_RET_UNHANDLED = 1,  /* 未处理（因守卫条件失败） */
    Q_RET_HANDLED   = 2,  /* 已处理 */
    Q_RET_TRAN      = 3,  /* 状态转换 */
    Q_RET_IGNORED   = 5   /* 忽略事件 */
};

/* QHsm — 层次状态机基类 */
typedef struct {
    QStateHandler state;   /* 当前活动状态 */
    QStateHandler temp;    /* 临时存储（转换目标/父状态） */
} QHsm;

/* 宏：转换到目标状态 */
#define Q_TRAN(target_) \
    ((me)->temp = (QStateHandler)(target_), (QState)Q_RET_TRAN)

/* 宏：委托给父状态 */
#define Q_SUPER(super_) \
    ((me)->temp = (QStateHandler)(super_), (QState)Q_RET_SUPER)

#define Q_HANDLED()   ((QState)Q_RET_HANDLED)
#define Q_UNHANDLED() ((QState)Q_RET_UNHANDLED)

/* 初始化HSM — 执行顶层初始转换 */
void QHsm_init(QHsm *me, QStateHandler initial) {
    QStateHandler path[8];
    size_t ip = 0;
    
    me->temp = initial;
    QState r = (*me->temp)(me, NULL);  /* 执行初始转换 */
    
    /* 构建入口路径 */
    do {
        path[ip++] = me->temp;
        (void)(*me->temp)(me, NULL);  /* 查询父状态 */
    } while (me->temp != me->state && ip < 8);
    
    /* 执行入口动作 */
    while (ip > 0) {
        --ip;
        (void)(*path[ip])(me, &(QEvt){Q_ENTRY_SIG, 0, 0});
    }
    
    me->state = path[0];
}

/* 事件分发 — 层次遍历状态树 */
void QHsm_dispatch(QHsm *me, QEvt const *e) {
    QStateHandler path[8];
    size_t ip = 8;
    QStateHandler s = me->state;
    
    me->temp = s;
    QState r;
    
    /* 自底向上尝试处理事件 */
    do {
        s = me->temp;
        path[--ip] = s;
        r = (*s)(me, e);
        
        if (r == Q_RET_UNHANDLED) {
            r = (*s)(me, NULL);  /* 查询父状态 */
        }
    } while (r == Q_RET_SUPER);
    
    if (r == Q_RET_TRAN) {
        /* 执行状态转换 */
        /* 1. 退出当前状态到转换源 */
        for (size_t i = 7; i > ip; --i) {
            (void)(*path[i])(me, &(QEvt){Q_EXIT_SIG, 0, 0});
        }
        
        /* 2. 进入目标状态 */
        path[0] = me->temp;
        ip = 1;
        me->temp = path[0];
        (void)(*me->temp)(me, NULL);  /* 查询父状态 */
        
        while (me->temp != s && ip < 8) {
            path[ip++] = me->temp;
            (void)(*me->temp)(me, NULL);
        }
        
        while (ip > 0) {
            --ip;
            (void)(*path[ip])(me, &(QEvt){Q_ENTRY_SIG, 0, 0});
        }
        
        me->state = path[0];
    }
}

/* ================================================================
 * 第3层：Active Object框架 (QF — QP Framework)
 * ================================================================
 * QP/C的Active Object模式：
 * - 每个AO有独立事件队列（FIFO）
 * - 通过事件发布/订阅解耦
 * - 优先级调度（QP支持最多64个AO）
 * - 内存池分配动态事件（零碎片）
 */

#define MAX_AO 8
#define QUEUE_SIZE 16

/* 事件队列 — 环形缓冲区 */
typedef struct {
    QEvt *ring[QUEUE_SIZE];
    uint8_t head;
    uint8_t tail;
    uint8_t count;
} EventQueue;

void EQ_init(EventQueue *eq) {
    eq->head = eq->tail = eq->count = 0;
}

bool EQ_post(EventQueue *eq, QEvt *e) {
    if (eq->count >= QUEUE_SIZE) return false;
    eq->ring[eq->head] = e;
    eq->head = (eq->head + 1) % QUEUE_SIZE;
    eq->count++;
    return true;
}

QEvt *EQ_get(EventQueue *eq) {
    if (eq->count == 0) return NULL;
    QEvt *e = eq->ring[eq->tail];
    eq->tail = (eq->tail + 1) % QUEUE_SIZE;
    eq->count--;
    return e;
}

/* 内存池 — 固定大小块分配器（QP/C核心设计） */
typedef struct {
    void **start;
    void **freeHead;
    uint16_t blockSize;
    uint16_t nFree;
    uint16_t nMin;
} MemoryPool;

void MP_init(MemoryPool *mp, void *storage, uint16_t poolSize, uint16_t blkSize) {
    mp->start = (void **)storage;
    mp->blockSize = blkSize;
    mp->nFree = poolSize / blkSize;
    mp->nMin = mp->nFree;
    
    /* 构建空闲链表 */
    uint8_t *p = (uint8_t *)storage;
    void **prev = NULL;
    for (uint16_t i = 0; i < mp->nFree; i++) {
        void **block = (void **)(p + i * blkSize);
        *block = prev;
        prev = block;
    }
    mp->freeHead = prev;
}

void *MP_get(MemoryPool *mp) {
    if (mp->freeHead == NULL) return NULL;
    void *block = mp->freeHead;
    mp->freeHead = *(void **)block;
    mp->nFree--;
    if (mp->nFree < mp->nMin) mp->nMin = mp->nFree;
    return block;
}

void MP_put(MemoryPool *mp, void *block) {
    *(void **)block = mp->freeHead;
    mp->freeHead = block;
    mp->nFree++;
}

/* Active Object 基类 */
typedef struct {
    QHsm hsm;              /* 继承层次状态机 */
    uint8_t prio;          /* 优先级 */
    EventQueue queue;      /* 事件队列 */
    void (*start)(void*);  /* 启动回调 */
} QActive;

/* 框架全局状态 */
typedef struct {
    QActive *active[MAX_AO];  /* 已注册的AO */
    uint8_t numActive;
    MemoryPool pool;          /* 事件内存池 */
    uint8_t poolStorage[1024];/* 内存池存储 */
} QFramework;

QFramework qf;

void QF_init(void) {
    memset(&qf, 0, sizeof(qf));
    MP_init(&qf.pool, qf.poolStorage, sizeof(qf.poolStorage), sizeof(MyEvent));
}

void QF_add(QActive *ao) {
    if (qf.numActive < MAX_AO) {
        qf.active[qf.numActive++] = ao;
    }
}

/* 分配动态事件（QP/C的Q_NEW宏） */
QEvt *QF_new(uint16_t sig) {
    MyEvent *e = (MyEvent *)MP_get(&qf.pool);
    if (e) {
        e->super.sig = sig;
        e->super.poolNum = 1;
        e->super.refCtr = 0;
    }
    return &e->super;
}

/* 垃圾回收（QP/C的QF_gc） */
void QF_gc(QEvt *e) {
    if (e && e->poolNum > 0 && e->refCtr == 0) {
        MP_put(&qf.pool, e);
    }
}

/* 发布事件到所有订阅者（QP/C的QF_publish） */
void QF_publish(QEvt *e) {
    for (uint8_t i = 0; i < qf.numActive; i++) {
        if (qf.active[i]) {
            EQ_post(&qf.active[i]->queue, e);
        }
    }
}

/* 主循环 — 运行所有Active Object */
void QF_run(void) {
    printf("[QF] 框架启动，%d个Active Object\n", qf.numActive);
    
    for (int cycle = 0; cycle < 5; cycle++) {
        printf("\n--- 周期 %d ---\n", cycle + 1);
        
        /* 向所有AO发送TICK事件 */
        QEvt tickEvt = {Q_USER_SIG, 0, 0};
        QF_publish(&tickEvt);
        
        /* 处理每个AO的事件队列 */
        for (uint8_t i = 0; i < qf.numActive; i++) {
            QActive *ao = qf.active[i];
            QEvt *e;
            while ((e = EQ_get(&ao->queue)) != NULL) {
                printf("[AO#%d] 处理事件 sig=%d\n", ao->prio, e->sig);
                QHsm_dispatch(&ao->hsm, e);
                QF_gc(e);
            }
        }
    }
}

/* ================================================================
 * 示例：LED控制器 — 层次状态机演示
 * ================================================================
 * 状态层次:
 *   top
 *    └── LedController (初始→Off)
 *          ├── Off (按按钮→On)
 *          └── On  (按按钮→Off, 双击→Blinking)
 *                └── Blinking (超时→On)
 */

/* 用户信号 */
enum {
    SIG_BUTTON_PRESS = Q_USER_SIG,
    SIG_BUTTON_DOUBLE,
    SIG_TIMEOUT,
    SIG_TICK
};

/* LED控制器对象 */
typedef struct {
    QActive super;       /* 继承Active Object */
    uint8_t brightness;  /* 亮度状态 */
    uint8_t blinkCount;  /* 闪烁计数 */
} LedController;

/* 状态处理函数声明 */
static QState LedController_initial(void *me, QEvt const *e);
static QState LedController_off(void *me, QEvt const *e);
static QState LedController_on(void *me, QEvt const *e);
static QState LedController_blinking(void *me, QEvt const *e);

/* 顶层状态 — 初始转换到Off */
static QState LedController_initial(void *me, QEvt const *e) {
    (void)e;
    printf("[LED] 初始化 → Off状态\n");
    return Q_TRAN(LedController_off);
}

/* Off状态 */
static QState LedController_off(void *me, QEvt const *e) {
    LedController *self = (LedController *)me;
    
    if (!e) {  /* 查询父状态 */
        return Q_SUPER(LedController_on);  /* 父状态是On（演示用） */
    }
    
    switch (e->sig) {
        case Q_ENTRY_SIG:
            printf("[LED-Off] 进入 — LED熄灭\n");
            self->brightness = 0;
            return Q_HANDLED();
        
        case Q_EXIT_SIG:
            printf("[LED-Off] 退出\n");
            return Q_HANDLED();
        
        case SIG_BUTTON_PRESS:
            printf("[LED-Off] 按钮按下 → 切换到On\n");
            return Q_TRAN(LedController_on);
        
        default:
            return Q_UNHANDLED();
    }
}

/* On状态 */
static QState LedController_on(void *me, QEvt const *e) {
    LedController *self = (LedController *)me;
    
    if (!e) {  /* 查询父状态 */
        return Q_SUPER(NULL);  /* 顶层状态 */
    }
    
    switch (e->sig) {
        case Q_ENTRY_SIG:
            printf("[LED-On] 进入 — LED亮起 (亮度=%d)\n", self->brightness);
            return Q_HANDLED();
        
        case Q_EXIT_SIG:
            printf("[LED-On] 退出\n");
            return Q_HANDLED();
        
        case SIG_BUTTON_PRESS:
            printf("[LED-On] 按钮按下 → 切换到Off\n");
            return Q_TRAN(LedController_off);
        
        case SIG_BUTTON_DOUBLE:
            printf("[LED-On] 双击 → 进入Blinking模式\n");
            self->blinkCount = 3;
            return Q_TRAN(LedController_blinking);
        
        default:
            return Q_UNHANDLED();
    }
}

/* Blinking状态（On的子状态） */
static QState LedController_blinking(void *me, QEvt const *e) {
    LedController *self = (LedController *)me;
    
    if (!e) {
        return Q_SUPER(LedController_on);  /* 父状态是On */
    }
    
    switch (e->sig) {
        case Q_ENTRY_SIG:
            printf("[LED-Blink] 进入 — 开始闪烁 (%d次)\n", self->blinkCount);
            return Q_HANDLED();
        
        case Q_EXIT_SIG:
            printf("[LED-Blink] 退出\n");
            return Q_HANDLED();
        
        case SIG_TICK:
            self->blinkCount--;
            printf("[LED-Blink] 闪烁! 剩余=%d\n", self->blinkCount);
            if (self->blinkCount == 0) {
                printf("[LED-Blink] 闪烁结束 → 回到On\n");
                return Q_TRAN(LedController_on);
            }
            return Q_HANDLED();
        
        default:
            return Q_UNHANDLED();
    }
}

/* ================================================================
 * 主函数 — 演示运行
 * ================================================================ */
int main(void) {
    printf("========================================\n");
    printf(" QP/C Active Object + HSM 概念演示\n");
    printf(" 学习自: QuantumLeaps/qpc (ARM Cortex-M)\n");
    printf("========================================\n\n");
    
    /* 初始化框架 */
    QF_init();
    
    /* 创建LED控制器Active Object */
    static LedController ledCtrl;
    memset(&ledCtrl, 0, sizeof(ledCtrl));
    ledCtrl.super.prio = 1;
    ledCtrl.super.hsm.state = LedController_initial;
    
    /* 初始化HSM */
    QHsm_init(&ledCtrl.super.hsm, LedController_initial);
    
    /* 注册到框架 */
    QF_add(&ledCtrl.super);
    
    /* 运行框架（5个周期） */
    QF_run();
    
    printf("\n========================================\n");
    printf(" 演示结束\n");
    printf("========================================\n");
    return 0;
}
