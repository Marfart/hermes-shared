# 公海客户全量爬取 - /rapi/d/customers/public

## API端点

```
GET /rapi/d/customers/public?num={page}&paging=true&size=500&sortColumn=lastTransferTime&sortType=desc
```

## 关键参数

| 参数 | 值 | 说明 |
|------|-----|------|
| num | 页码（从1开始） | 翻页用 |
| paging | true | 必须 |
| size | 最大500 | 推荐500减少请求次数 |
| sortColumn | lastTransferTime | 按转入公海时间排序 |
| sortType | desc | 降序 |

## 数据规模

- 总记录：66,224条
- size=500时共133页
- 爬取速度：约1000条/秒
- 预计耗时：~70秒

## ⚠️ 常见错误

- `/rapi/d/customers?tab=1` → 返回"我的客户"（1957条），不是公海！
- `/rapi/d/customers?tab=1&isCommonUse=true` → 同样是1957条
- 必须用 `/rapi/d/customers/public` 端点

## CDP浏览器内fetch爬取

通过CDP WebSocket在浏览器上下文内执行fetch，自动携带Cookie和Session：

```python
cmd = {
    "id": page + 1000,
    "method": "Runtime.evaluate",
    "params": {
        "expression": f"""
            (async () => {{
                let r = await fetch('/rapi/d/customers/public?num={page}&paging=true&size=500&sortColumn=lastTransferTime&sortType=desc');
                let j = await r.json();
                return JSON.stringify({{values: j.data?.values || []}});
            }})()
        """,
        "awaitPromise": True,
        "returnByValue": True
    }
}
```

## 公海客户特有字段

| 字段名 | 中文名 | 说明 |
|--------|--------|------|
| remainingTime | 剩余时间 | 如"19天1小时" |
| lastTransferTime | 转入公海时间 | 毫秒级timestamp |
| lastTransferInfo | 转入公海信息 | |
| publicGroup | 所属部门 | 如"外贸部" |
| activity | 最近活动 | 如"营销信：RE:xxx" |
| activityType | 活动类型 | 如"edmemail" |
| businessType | 业务类型 | 如"系统集成商" |

## Excel报表结构

- Sheet 1: Dashboard（KPI概览 + Top20国家）
- Sheet 2: 全部客户（66,224行 × 25核心字段）
- Sheet 3: 按业务员统计（12人）
- Sheet 4: 按国家地区统计（202个）
- Sheet 5: 按客户来源统计（240个）
- Sheet 6: 按业务类型统计（8个）

## 数据清洗要点

1. **时间戳转换**：毫秒级Unix timestamp → `YYYY-MM-DD HH:MM`
2. **非打印字符**：openpyxl会因控制字符崩溃，必须清洗
3. **列表转字符串**：tags等数组字段用 `', '.join()` 转换
