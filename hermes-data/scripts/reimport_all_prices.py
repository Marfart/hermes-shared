#!/usr/bin/env python3
"""Re-import ALL prices from ALL source files with correct tier mapping"""
import sqlite3, xlrd, openpyxl, os

DB_PATH = r"C:\Users\Admin\AppData\Local\hermes\scripts\bliiot.db"
conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row

# Clean slate
conn.execute("DELETE FROM prices")
print("Prices cleared")

# Tier IDs
tiers = {}
for t in conn.execute("SELECT id, name FROM price_tiers").fetchall():
    tiers[t["name"]] = t["id"]
print(f"Tiers: {tiers}")

def safe_price(val):
    if isinstance(val, (int, float)):
        return round(float(val), 2) if float(val) > 0 else None
    if isinstance(val, str):
        v = val.strip().replace("$", "").replace(",", "")
        try:
            f = float(v)
            return round(f, 2) if f > 0 else None
        except:
            return None
    return None

def find_prod(model, source=None):
    """Find a product by model, optionally filtered by source"""
    if source:
        r = conn.execute("SELECT rowid AS rid FROM products WHERE model=? AND source_file=?", (model, source)).fetchone()
        if r:
            return r["rid"]
    r = conn.execute("SELECT rowid AS rid FROM products WHERE model=?", (model,)).fetchone()
    return r["rid"] if r else None

def set_price(pid, tier_name, val):
    p = safe_price(val)
    if p is None:
        return False
    tid = tiers.get(tier_name)
    if not tid:
        return False
    conn.execute("INSERT OR REPLACE INTO prices (product_id, tier_id, price_usd) VALUES (?,?,?)", (pid, tid, p))
    return True

def set_p(model, source, tier_name, val):
    pid = find_prod(model, source)
    if pid is None:
        pid = find_prod(model)
    if pid is None:
        return False
    return set_price(pid, tier_name, val)

# ============ 1. ARMxy files (BL310-BL460) ============
print("\n1. ARMxy prices...")
ship_dir = r"C:\Users\Admin\Desktop\Working\出货\报价数据"
arm_files = [f for f in os.listdir(ship_dir) if f.startswith("202511 ARMxy") and f.endswith(".xls")]
arm_files.sort()

for fname in arm_files:
    fpath = ship_dir + "\\" + fname
    wb = xlrd.open_workbook(fpath)
    ws = wb.sheet_by_index(0)
    hr = None
    for r in range(5, 20):
        if str(ws.cell_value(r, 0)).strip().lower() == "model":
            hr = r; break
    if hr is None:
        continue
    cnt = 0
    SKIP = {"kernel", "note", "file system", "buildroot", "qt", "gui development",
            "you can choose", "x series", "y series", "model", "gui development tool"}
    for r in range(hr + 1, ws.nrows):
        m = str(ws.cell_value(r, 0)).strip()
        if not m or m == "0.0" or len(m) < 3:
            continue
        if m.lower() in SKIP:
            continue
        ok = False
        if set_p(m, fname, "Sample", ws.cell_value(r, 9)):
            ok = True
        if set_p(m, fname, "<100pcs", ws.cell_value(r, 7)):
            ok = True
        if set_p(m, fname, ">=100pcs", ws.cell_value(r, 8)):
            ok = True
        if ok:
            cnt += 1
    print(f"  {fname[:55]:55s} {cnt:4d}")

# ============ 2. RTU & Router ============
print("\n2. RTU & Router...")
fpath = r"C:\Users\Admin\Desktop\Working\1.报价文件\202605 BLIIOT RTU&Router Price List.xls"
wb = xlrd.open_workbook(fpath)
ws = wb.sheet_by_name("Price List")
hr = None
for r in range(10):
    if str(ws.cell_value(r, 0)).strip().lower().startswith("model"):
        hr = r; break
cnt = 0
src = "202605 BLIIOT RTU&Router Price List.xls"
for r in range(hr + 1, ws.nrows):
    m = str(ws.cell_value(r, 0)).strip()
    if not m or m == "0.0":
        continue
    ok = False
    if set_p(m, src, "Sample", ws.cell_value(r, 4)):
        ok = True
    if set_p(m, src, "<100pcs", ws.cell_value(r, 5)):
        ok = True
    if set_p(m, src, ">=100pcs", ws.cell_value(r, 7)):
        ok = True
    if ok:
        cnt += 1
print(f"  {cnt} products")

# ============ 3. IIoT Gateways (BL120) ============
print("\n3. IIoT Gateways (BL120)...")
fpath = r"C:\Users\Admin\Desktop\Working\1.报价文件\202605 BLIIOT IIoT Gateways &BL116&BL118 Price List.xls"
wb = xlrd.open_workbook(fpath)
ws = wb.sheet_by_name("IIoT Gateways")
cnt = 0
src = "202605 BLIIOT IIoT Gateways &BL116&BL118 Price List.xls"
for r in range(1, ws.nrows):
    m = str(ws.cell_value(r, 2)).strip()
    if not m or m == "0.0":
        continue
    ok = False
    if set_p(m, src, "Sample", ws.cell_value(r, 3)):
        ok = True
    if set_p(m, src, "<100pcs", ws.cell_value(r, 4)):
        ok = True
    if set_p(m, src, ">=100pcs", ws.cell_value(r, 5)):
        ok = True
    if ok:
        cnt += 1
print(f"  {cnt} products")

# ============ 4. BL116 ============
print("\n4. BL116...")
ws = wb.sheet_by_name("BL116")
hr = None
for r in range(20):
    v0 = str(ws.cell_value(r, 0)).strip().lower()
    v1 = str(ws.cell_value(r, 1)).strip().lower()
    if v0.startswith("model") or v1.startswith("model"):
        hr = r; break
cnt = 0
if hr:
    for r in range(hr + 1, ws.nrows):
        m = str(ws.cell_value(r, 0)).strip() or str(ws.cell_value(r, 1)).strip()
        if not m or m == "0.0" or len(m) < 3:
            continue
        ok = False
        if set_p(m, src, "Sample", ws.cell_value(r, 3)):
            ok = True
        if set_p(m, src, "<100pcs", ws.cell_value(r, 4)):
            ok = True
        if set_p(m, src, ">=100pcs", ws.cell_value(r, 6)):
            ok = True
        if ok:
            cnt += 1
print(f"  {cnt} products")

# ============ 5. BL118 ============
print("\n5. BL118...")
ws = wb.sheet_by_name("BL118")
hr = None
for r in range(20):
    v0 = str(ws.cell_value(r, 0)).strip().lower()
    v1 = str(ws.cell_value(r, 1)).strip().lower()
    if v0.startswith("model") or v1.startswith("model"):
        hr = r; break
cnt = 0
SKIP = {"model", "note", "kernel", "product naming", "for example", "the ",
        "this quotation", "series model", "if a", "gui development"}
if hr:
    for r in range(hr + 1, ws.nrows):
        m = str(ws.cell_value(r, 0)).strip() or str(ws.cell_value(r, 1)).strip()
        if not m or m == "0.0" or len(m) < 3:
            continue
        if any(s in m.lower() for s in SKIP):
            continue
        ok = False
        if set_p(m, src, "Sample", ws.cell_value(r, 3)):
            ok = True
        if set_p(m, src, "<100pcs", ws.cell_value(r, 4)):
            ok = True
        if set_p(m, src, ">=100pcs", ws.cell_value(r, 6)):
            ok = True
        if ok:
            cnt += 1
print(f"  {cnt} products")

# ============ 6. Master Price List 20240527 ============
print("\n6. BLIIoT Price List 20240527...")
fpath = r"C:\Users\Admin\Desktop\Working\1.报价文件\BLIIoT Price List 20240527.xls"
wb = xlrd.open_workbook(fpath)
ws = wb.sheet_by_name("Price List")
hr = None
for r in range(10):
    if str(ws.cell_value(r, 0)).strip().lower().startswith("model"):
        hr = r; break
cnt = 0
src = "BLIIoT Price List 20240527.xls"
for r in range(hr + 1, ws.nrows):
    m = str(ws.cell_value(r, 0)).strip()
    if not m or m == "0.0":
        continue
    ok = False
    if set_p(m, src, "Sample", ws.cell_value(r, 4)):
        ok = True
    if set_p(m, src, "<100pcs", ws.cell_value(r, 5)):
        ok = True
    if set_p(m, src, ">=100pcs", ws.cell_value(r, 7)):
        ok = True
    if ok:
        cnt += 1
print(f"  {cnt} products")

# ============ 7. Other XLS files ============
print("\n7. Other XLS quote files...")
other_xls = [
    (r"C:\Users\Admin\Desktop\Working\出货\报价数据\BLIIoT BL16 Series Industrial Ethernet Switch Price List.xls", "BLIIoT BL16 Series Industrial Ethernet Switch Price List.xls", 4),
    (r"C:\Users\Admin\Desktop\Working\1.报价文件\202511 BL118 Node-RED Edge Gateway Price List.xls", "202511 BL118 Node-RED Edge Gateway Price List.xls", 4),
    (r"C:\Users\Admin\Desktop\Working\1.报价文件\202511 IOy Series Edge IO Module Price List.xls", "202511 IOy Series Edge IO Module Price List.xls", 4),
    (r"C:\Users\Admin\Desktop\Working\1.报价文件\202605 BLIIOT IOy Series Edge IO Module Price List.xls", "202605 BLIIOT IOy Series Edge IO Module Price List.xls", 4),
]
for fpath, fname, sc in other_xls:
    try:
        wb = xlrd.open_workbook(fpath)
        ws = wb.sheet_by_index(0)
        hr = None
        for r in range(15):
            v = str(ws.cell_value(r, 0)).strip().lower()
            if v.startswith("model") or v.startswith("industrial"):
                hr = r; break
        if hr is None:
            continue
        cnt = 0
        for r in range(hr + 1, ws.nrows):
            model = str(ws.cell_value(r, 2)).strip() or str(ws.cell_value(r, 0)).strip()
            if not model or model == "0.0" or len(model) < 3:
                continue
            ok = False
            if set_p(model, fname, "Sample", ws.cell_value(r, sc)):
                ok = True
            if set_p(model, fname, "<100pcs", ws.cell_value(r, sc + 1)):
                ok = True
            if set_p(model, fname, ">=100pcs", ws.cell_value(r, min(sc + 3, ws.ncols - 1))):
                ok = True
            if ok:
                cnt += 1
        print(f"  {fname[:55]:55s} {cnt:4d}")
    except Exception as e:
        print(f"  {fname[:55]:55s} ERROR: {e}")

# ============ 8. 202512 IIoT Gateways ============
print("\n8. 202512 IIoT Gateways...")
fpath = r"C:\Users\Admin\Desktop\Working\1.报价文件\202512 IIoT Gateways Price List.xls"
wb = xlrd.open_workbook(fpath)
ws = wb.sheet_by_index(0)
cnt = 0
src = "202512 IIoT Gateways Price List.xls"
for r in range(1, ws.nrows):
    model = str(ws.cell_value(r, 2)).strip()
    if not model or model == "0.0":
        continue
    ok = False
    if set_p(model, src, "Sample", ws.cell_value(r, 3)):
        ok = True
    if set_p(model, src, "<100pcs", ws.cell_value(r, 4)):
        ok = True
    if set_p(model, src, ">=100pcs", ws.cell_value(r, 5)):
        ok = True
    if ok:
        cnt += 1
print(f"  {cnt} products")

# ============ 9. DB Junction Box ============
print("\n9. DB分线盒...")
fpath = r"C:\Users\Admin\Desktop\Working\1.报价文件\DB系列分线盒报价单USD.xlsx"
wb = openpyxl.load_workbook(fpath, read_only=True, data_only=True)
ws = wb["Sheet1"]
cnt = 0
src = "DB系列分线盒报价单USD.xlsx"
for i, row in enumerate(ws.iter_rows(values_only=True)):
    if i < 2:
        continue
    if not row or not row[1]:
        continue
    model = str(row[1]).strip()
    if not model or model == "None":
        continue
    ok = False
    if set_p(model, src, "Sample", row[2]):
        ok = True
    if set_p(model, src, "<100pcs", row[3]):
        ok = True
    if set_p(model, src, ">=100pcs", row[4]):
        ok = True
    if ok:
        cnt += 1
print(f"  {cnt} products")
wb.close()

# ============ 10. 202512 ARMxy xlsx ============
print("\n10. 202512 ARMxy xlsx...")
fpath = r"C:\Users\Admin\Desktop\Working\1.报价文件\202512 ARMxy Series Embedded Computer Price List.xlsx"
wb = openpyxl.load_workbook(fpath, read_only=True, data_only=True)
ws = wb[wb.sheetnames[0]]
hr = None
for i, row in enumerate(ws.iter_rows(values_only=True)):
    if row and str(row[0] or "").strip().lower() == "model":
        hr = i; break
cnt = 0
src = "202512 ARMxy Series Embedded Computer Price List.xlsx"
if hr:
    for i, row in enumerate(ws.iter_rows(values_only=True)):
        if i <= hr:
            continue
        if not row or not row[0]:
            continue
        model = str(row[0]).strip()
        if not model or model == "None" or len(model) < 3:
            continue
        ok = False
        if set_p(model, src, "Sample", row[4]):
            ok = True
        if set_p(model, src, "<100pcs", row[5]):
            ok = True
        if set_p(model, src, ">=100pcs", row[6]):
            ok = True
        if ok:
            cnt += 1
print(f"  {cnt} products")
wb.close()

# ============ Apply rule: missing Sample = use <100pcs ============
print("\n11. Applying rule: missing Sample = <100pcs price...")
fixed = 0
for r in conn.execute("""
    SELECT pr.product_id, pr.price_usd
    FROM prices pr
    JOIN price_tiers pt ON pt.id = pr.tier_id AND pt.name = '<100pcs'
    WHERE NOT EXISTS (
        SELECT 1 FROM prices pr2
        JOIN price_tiers pt2 ON pt2.id = pr2.tier_id AND pt2.name = 'Sample'
        WHERE pr2.product_id = pr.product_id
    )
""").fetchall():
    set_price(r["product_id"], "Sample", r["price_usd"])
    fixed += 1
print(f"  {fixed} products fixed")

conn.commit()

# ============ Final Audit ============
print("\n" + "=" * 60)
print("FINAL AUDIT")
print("=" * 60)
total = 0
for r in conn.execute("""
    SELECT p.source_file,
           COUNT(DISTINCT p.rowid) as total,
           COUNT(DISTINCT CASE WHEN s.price_usd IS NOT NULL THEN p.rowid END) as with_sample,
           COUNT(DISTINCT CASE WHEN h.price_usd IS NOT NULL THEN p.rowid END) as with_100,
           COUNT(DISTINCT CASE WHEN o.price_usd IS NOT NULL THEN p.rowid END) as with_over100
    FROM products p
    LEFT JOIN prices s ON s.product_id = p.rowid AND s.tier_id = ?
    LEFT JOIN prices h ON h.product_id = p.rowid AND h.tier_id = ?
    LEFT JOIN prices o ON o.product_id = p.rowid AND o.tier_id = ?
    WHERE p.source_file IS NOT NULL
    GROUP BY p.source_file
    ORDER BY p.source_file
""", (tiers.get("Sample"), tiers.get("<100pcs"), tiers.get(">=100pcs"))).fetchall():
    fn = (r["source_file"] or "N/A")[:55]
    print(f"  {fn:55s} | {r['total']:>4d} prods | S:{r['with_sample']:>4d} | <100:{r['with_100']:>4d} | >=100:{r['with_over100']:>4d}")
    total += r["total"]

no_price = conn.execute("SELECT COUNT(*) as c FROM products p WHERE NOT EXISTS (SELECT 1 FROM prices pr WHERE pr.product_id = p.rowid)").fetchone()
print(f"\n  Total products: {total}")
print(f"  Products with NO prices: {no_price['c']}")

# Verify our 4 components
print("\n" + "=" * 60)
print("VERIFICATION: BL335A-SOM335-X6-Y01")
print("=" * 60)
for model in ["BL335A", "SOM335", "X6", "Y01"]:
    prices = conn.execute("""
        SELECT pt.name, pr.price_usd
        FROM products p
        JOIN prices pr ON pr.product_id = p.rowid
        JOIN price_tiers pt ON pt.id = pr.tier_id
        WHERE p.model = ?
        ORDER BY pt.sort_order
    """, (model,)).fetchall()
    if prices:
        line = f"  {model:10s}: "
        line += " | ".join([f"{p['name']}=${p['price_usd']:.2f}" for p in prices])
        print(line)
    else:
        print(f"  {model:10s}: NO PRICES")

conn.close()
print("\nDONE!")
