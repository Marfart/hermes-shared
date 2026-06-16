#!/usr/bin/env python3
"""Re-import ALL prices with CORRECT per-file tier names"""
import sqlite3, xlrd, openpyxl, os, json

DB_PATH = r"C:\Users\Admin\AppData\Local\hermes\scripts\bliiot.db"
conn = sqlite3.connect(DB_PATH)

# Ensure price_tiers has all original names
print("Rebuilding price_tiers...")
conn.executescript("""
    DROP TABLE IF EXISTS price_tiers;
    CREATE TABLE price_tiers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL UNIQUE,
        min_qty INTEGER,
        max_qty INTEGER,
        sort_order INTEGER DEFAULT 0
    );
    INSERT INTO price_tiers (name, min_qty, max_qty, sort_order) VALUES ('Sample', 1, 1, 1);
    INSERT INTO price_tiers (name, min_qty, max_qty, sort_order) VALUES ('Samples', 1, 1, 1);
    INSERT INTO price_tiers (name, min_qty, max_qty, sort_order) VALUES ('Online Store & Quotation', 1, 1, 1);
    INSERT INTO price_tiers (name, min_qty, max_qty, sort_order) VALUES ('50pcs', 50, 50, 2);
    INSERT INTO price_tiers (name, min_qty, max_qty, sort_order) VALUES ('<50Pcs', 1, 49, 2);
    INSERT INTO price_tiers (name, min_qty, max_qty, sort_order) VALUES ('>50Pcs', 50, 99, 3);
    INSERT INTO price_tiers (name, min_qty, max_qty, sort_order) VALUES ('100pcs', 100, 100, 4);
    INSERT INTO price_tiers (name, min_qty, max_qty, sort_order) VALUES ('100PCS', 100, 100, 4);
    INSERT INTO price_tiers (name, min_qty, max_qty, sort_order) VALUES ('<100pcs', 10, 99, 2);
    INSERT INTO price_tiers (name, min_qty, max_qty, sort_order) VALUES ('>100Pcs', 100, 499, 4);
    INSERT INTO price_tiers (name, min_qty, max_qty, sort_order) VALUES ('>=100pcs', 100, NULL, 5);
    INSERT INTO price_tiers (name, min_qty, max_qty, sort_order) VALUES ('500pcs', 500, 500, 6);
    INSERT INTO price_tiers (name, min_qty, max_qty, sort_order) VALUES ('500PCS', 500, 500, 6);
    INSERT INTO price_tiers (name, min_qty, max_qty, sort_order) VALUES ('>500Pcs', 500, NULL, 6);
""")
conn.commit()

# Get tier IDs
tiers = {}
for t in conn.execute("SELECT id, name FROM price_tiers").fetchall():
    tiers[t[1]] = t[0]
print(f"Tiers: {json.dumps(tiers)}")

# Delete old prices
conn.execute("DELETE FROM prices")
print("Old prices cleared\n")

def sp(val):
    if isinstance(val, (int, float)):
        return round(float(val), 2) if float(val) > 0 else None
    if isinstance(val, str):
        try:
            f = float(val.strip().replace("$","").replace(",",""))
            return round(f, 2) if f > 0 else None
        except:
            return None
    return None

def find_prod(model, source=None):
    if source:
        r = conn.execute("SELECT rowid FROM products WHERE model=? AND source_file=?", (model, source)).fetchone()
        if r: return r[0]
    r = conn.execute("SELECT rowid FROM products WHERE model=? LIMIT 1", (model,)).fetchone()
    return r[0] if r else None

def imp_price(model, source, tier_name, col_val):
    p = sp(col_val)
    if p is None: return False
    tid = tiers.get(tier_name)
    if not tid: return False
    pid = find_prod(model, source)
    if not pid:
        pid = find_prod(model)
    if not pid: return False
    conn.execute("INSERT OR REPLACE INTO prices (product_id, tier_id, price_usd) VALUES (?,?,?)", (pid, tid, p))
    return True

# ===== 1. IIoT Gateways (BL120) =====
print("1. IIoT Gateways (BL120): Sample | 50pcs | 100pcs | 500pcs")
fpath = r"C:\Users\Admin\Desktop\Working\1.报价文件\202605 BLIIOT IIoT Gateways &BL116&BL118 Price List.xls"
wb = xlrd.open_workbook(fpath)
ws = wb.sheet_by_name("IIoT Gateways")
src = "202605 BLIIOT IIoT Gateways &BL116&BL118 Price List.xls"
cnt = 0
tier_cols = [("Sample", 3), ("50pcs", 4), ("100pcs", 5), ("500pcs", 6)]
for r in range(1, ws.nrows):
    model = str(ws.cell_value(r, 2)).strip()
    if not model or model == "0.0": continue
    for tn, col in tier_cols:
        if col < ws.ncols:
            imp_price(model, src, tn, ws.cell_value(r, col))
    cnt += 1
print(f"  {cnt} products")

# ===== 2. 202512 IIoT Gateways (旧版) =====
print("\n2. 202512 IIoT Gateways: Sample | 50pcs | 100pcs | 500pcs")
fpath = r"C:\Users\Admin\Desktop\Working\1.报价文件\202512 IIoT Gateways Price List.xls"
wb = xlrd.open_workbook(fpath)
ws = wb.sheet_by_index(0)
src = "202512 IIoT Gateways Price List.xls"
cnt = 0
for r in range(1, ws.nrows):
    model = str(ws.cell_value(r, 2)).strip()
    if not model or model == "0.0": continue
    for tn, col in tier_cols:
        if col < ws.ncols:
            imp_price(model, src, tn, ws.cell_value(r, col))
    cnt += 1
print(f"  {cnt} products")

# ===== 3. RTU & Router =====
print("\n3. RTU & Router: Samples | <50Pcs | >50Pcs | >100Pcs | >500Pcs")
fpath = r"C:\Users\Admin\Desktop\Working\1.报价文件\202605 BLIIOT RTU&Router Price List.xls"
wb = xlrd.open_workbook(fpath)
ws = wb.sheet_by_name("Price List")
src = "202605 BLIIOT RTU&Router Price List.xls"
hr = None
for r in range(10):
    if str(ws.cell_value(r, 0)).strip().lower().startswith("model"): hr = r; break
cnt = 0
rtu_tiers = [("Samples", 4), ("<50Pcs", 5), (">50Pcs", 6), (">100Pcs", 7), (">500Pcs", 8)]
for r in range(hr+1, ws.nrows):
    model = str(ws.cell_value(r, 0)).strip()
    if not model or model == "0.0": continue
    for tn, col in rtu_tiers:
        if col < ws.ncols:
            imp_price(model, src, tn, ws.cell_value(r, col))
    cnt += 1
print(f"  {cnt} products")

# ===== 4. BLIIoT Price List 20240527 =====
print("\n4. BLIIoT Price List 20240527: Samples | <50Pcs | >50Pcs | >100Pcs | >500Pcs")
fpath = r"C:\Users\Admin\Desktop\Working\1.报价文件\BLIIoT Price List 20240527.xls"
wb = xlrd.open_workbook(fpath)
ws = wb.sheet_by_name("Price List")
hr = None
for r in range(10):
    if str(ws.cell_value(r, 0)).strip().lower().startswith("model"): hr = r; break
src = "BLIIoT Price List 20240527.xls"
cnt = 0
for r in range(hr+1, ws.nrows):
    model = str(ws.cell_value(r, 0)).strip()
    if not model or model == "0.0": continue
    for tn, col in rtu_tiers:
        if col < ws.ncols:
            imp_price(model, src, tn, ws.cell_value(r, col))
    cnt += 1
print(f"  {cnt} products")

# ===== 5. ARMxy files =====
print("\n5. ARMxy files: <100pcs | >=100pcs | Online Store & Quotation")
ship_dir = r"C:\Users\Admin\Desktop\Working\出货\报价数据"
arm_files = sorted([f for f in os.listdir(ship_dir) if f.startswith("202511 ARMxy") and f.endswith(".xls")])
arm_tiers = [("Online Store & Quotation", 9), ("<100pcs", 7), (">=100pcs", 8)]
arm_total = 0
for fname in arm_files:
    wb = xlrd.open_workbook(ship_dir + "\\" + fname)
    ws = wb.sheet_by_index(0)
    hr = None
    for r in range(5, 20):
        if str(ws.cell_value(r, 0)).strip().lower() == "model": hr = r; break
    if hr is None: continue
    cnt = 0
    SKIP = {"kernel", "note", "file system", "buildroot", "qt", "gui development",
            "you can choose", "x series", "y series", "gui development tool"}
    for r in range(hr+1, ws.nrows):
        model = str(ws.cell_value(r, 0)).strip()
        if not model or model == "0.0" or len(model) < 2: continue
        if model.lower() in SKIP: continue
        
        # Y board section has TWO-COLUMN layout
        mu = model.upper()
        if (mu.startswith("Y") and len(model) >= 2 and model[1:].isdigit()):
            # Left Y board: <100pcs=Col2, >=100pcs=Col3
            imp_price(model, fname, "<100pcs", ws.cell_value(r, 2))
            imp_price(model, fname, ">=100pcs", ws.cell_value(r, 3))
            # Check right side
            rmodel = str(ws.cell_value(r, 5)).strip()
            if rmodel and rmodel.upper().startswith("Y") and len(rmodel) >= 2 and rmodel[1:].isdigit():
                imp_price(rmodel, fname, "<100pcs", ws.cell_value(r, 7))
                imp_price(rmodel, fname, ">=100pcs", ws.cell_value(r, 8))
            cnt += 1
        elif mu.startswith("X") and len(model) >= 2 and model[1:].isdigit():
            # X board: normal layout
            for tn, col in arm_tiers:
                if col < ws.ncols:
                    imp_price(model, fname, tn, ws.cell_value(r, col))
            cnt += 1
        else:
            # Main model + SOM: normal layout
            for tn, col in arm_tiers:
                if col < ws.ncols:
                    imp_price(model, fname, tn, ws.cell_value(r, col))
            cnt += 1
    print(f"  {fname[:50]:50s} {cnt:4d}")
    arm_total += cnt
print(f"  ARMxy total: {arm_total}")

# ===== 6. BL116 =====
print("\n6. BL116: Sample | <50Pcs | >50Pcs | >100Pcs | >500Pcs")
ws = wb.sheet_by_name("BL116")  # Note: using the last wb from above
hr = None
for r in range(20):
    v = str(ws.cell_value(r, 0)).strip().lower() or str(ws.cell_value(r, 1)).strip().lower()
    if v.startswith("model"): hr = r; break
cnt = 0
bl_tiers = [("Sample", 3), ("<50Pcs", 4), (">50Pcs", 5), (">100Pcs", 6), (">500Pcs", 7)]
if hr:
    for r in range(hr+1, ws.nrows):
        model = str(ws.cell_value(r, 0)).strip() or str(ws.cell_value(r, 1)).strip()
        if not model or model == "0.0" or len(model) < 3: continue
        for tn, col in bl_tiers:
            if col < ws.ncols:
                imp_price(model, src, tn, ws.cell_value(r, col))
        cnt += 1
print(f"  {cnt} products")

# ===== 7. BL118 =====
print("\n7. BL118: Sample | <50Pcs | >50Pcs | >100Pcs | >500Pcs")
ws = wb.sheet_by_name("BL118")
hr = None
for r in range(20):
    v0 = str(ws.cell_value(r, 0)).strip().lower()
    v1 = str(ws.cell_value(r, 1)).strip().lower()
    if v0.startswith("model") or v1.startswith("model"): hr = r; break
cnt = 0
SKIP2 = {"model", "note", "kernel", "product naming", "for example", "the ",
         "this quotation", "series model", "if a", "gui development"}
if hr:
    for r in range(hr+1, ws.nrows):
        model = str(ws.cell_value(r, 0)).strip() or str(ws.cell_value(r, 1)).strip()
        if not model or model == "0.0" or len(model) < 3: continue
        if any(s in model.lower() for s in SKIP2): continue
        for tn, col in bl_tiers:
            if col < ws.ncols:
                imp_price(model, src, tn, ws.cell_value(r, col))
        cnt += 1
print(f"  {cnt} products")

# ===== 8. Other XLS files =====
print("\n8. Other files...")
others = [
    (r"C:\Users\Admin\Desktop\Working\出货\报价数据\BLIIoT BL16 Series Industrial Ethernet Switch Price List.xls",
     "BLIIoT BL16 Series Industrial Ethernet Switch Price List.xls", [("Sample",4),("<50Pcs",5),(">50Pcs",6),(">100Pcs",7),(">500Pcs",8)]),
    (r"C:\Users\Admin\Desktop\Working\1.报价文件\202511 BL118 Node-RED Edge Gateway Price List.xls",
     "202511 BL118 Node-RED Edge Gateway Price List.xls", [("Sample",4),("<50Pcs",5),(">50Pcs",6),(">100Pcs",7),(">500Pcs",8)]),
    (r"C:\Users\Admin\Desktop\Working\1.报价文件\202511 IOy Series Edge IO Module Price List.xls",
     "202511 IOy Series Edge IO Module Price List.xls", [("Sample",4),("<50Pcs",5),(">50Pcs",6),(">100Pcs",7),(">500Pcs",8)]),
    (r"C:\Users\Admin\Desktop\Working\1.报价文件\202605 BLIIOT IOy Series Edge IO Module Price List.xls",
     "202605 BLIIOT IOy Series Edge IO Module Price List.xls", [("Sample",4),("<50Pcs",5),(">50Pcs",6),(">100Pcs",7),(">500Pcs",8)]),
]
for fpath, fname, tier_list in others:
    try:
        wb = xlrd.open_workbook(fpath)
        ws = wb.sheet_by_index(0)
        hr = None
        for r in range(15):
            v = str(ws.cell_value(r, 0)).strip().lower()
            if v.startswith("model") or v.startswith("industrial"): hr = r; break
        if hr is None:
            print(f"  {fname[:50]:50s} 0 (no header)")
            continue
        cnt = 0
        for r in range(hr+1, ws.nrows):
            model = str(ws.cell_value(r, 2)).strip() or str(ws.cell_value(r, 0)).strip()
            if not model or model == "0.0" or len(model) < 3: continue
            for tn, col in tier_list:
                if col < ws.ncols:
                    imp_price(model, fname, tn, ws.cell_value(r, col))
            cnt += 1
        print(f"  {fname[:50]:50s} {cnt:4d}")
    except Exception as e:
        print(f"  {fname[:50]:50s} ERROR: {e}")

# ===== 9. DB Junction Box =====
print("\n9. DB分线盒: Sample | 100PCS | 500PCS")
fpath = r"C:\Users\Admin\Desktop\Working\1.报价文件\DB系列分线盒报价单USD.xlsx"
wb = openpyxl.load_workbook(fpath, read_only=True, data_only=True)
ws = wb["Sheet1"]
cnt = 0
src = "DB系列分线盒报价单USD.xlsx"
for i, row in enumerate(ws.iter_rows(values_only=True)):
    if i < 2: continue
    if not row or not row[1]: continue
    model = str(row[1]).strip()
    if not model or model == "None": continue
    imp_price(model, src, "Sample", row[2])
    imp_price(model, src, "100PCS", row[3])
    imp_price(model, src, "500PCS", row[4])
    cnt += 1
print(f"  {cnt} products")
wb.close()

# ===== 10. 202512 ARMxy xlsx =====
print("\n10. 202512 ARMxy xlsx")
fpath = r"C:\Users\Admin\Desktop\Working\1.报价文件\202512 ARMxy Series Embedded Computer Price List.xlsx"
wb = openpyxl.load_workbook(fpath, read_only=True, data_only=True)
ws = wb[wb.sheetnames[0]]
hr = None
for i, row in enumerate(ws.iter_rows(values_only=True)):
    if row and str(row[0] or "").strip().lower() == "model": hr = i; break
cnt = 0
src = "202512 ARMxy Series Embedded Computer Price List.xlsx"
if hr:
    for i, row in enumerate(ws.iter_rows(values_only=True)):
        if i <= hr: continue
        if not row or not row[0]: continue
        model = str(row[0]).strip()
        if not model or model == "None" or len(model) < 3: continue
        imp_price(model, src, "Sample", row[4])
        imp_price(model, src, "<100pcs", row[5])
        imp_price(model, src, ">=100pcs", row[6])
        cnt += 1
print(f"  {cnt} products")
wb.close()

conn.commit()

# ===== Final Audit =====
print(f"\n{'='*60}")
print("FINAL AUDIT")
print(f"{'='*60}")

# Count total prices
total_prices = conn.execute("SELECT COUNT(*) FROM prices").fetchone()[0]
print(f"Total price records: {total_prices}")

# Check specific products
print(f"\n🎯 BL121W:")
bl121w = conn.execute("""
    SELECT p.model, p.version, p.source_file, pt.name as tier, pr.price_usd
    FROM products p
    JOIN prices pr ON pr.product_id = p.rowid
    JOIN price_tiers pt ON pt.id = pr.tier_id
    WHERE p.model='BL121W'
    ORDER BY p.source_file, pt.sort_order
""").fetchall()
for r in bl121w:
    print(f"  [{str(r[2])[:45]:45s}] {r[3]:15s} = ${r[4]:.2f}")

print(f"\n🎯 R40:")
r40 = conn.execute("""
    SELECT p.model, p.version, pt.name as tier, pr.price_usd
    FROM products p
    JOIN prices pr ON pr.product_id = p.rowid
    JOIN price_tiers pt ON pt.id = pr.tier_id
    WHERE p.model='R40'
    ORDER BY pt.sort_order
""").fetchall()
for r in r40:
    print(f"  {r[2]:15s} = ${r[3]:.2f}")

print(f"\n🎯 BL335A:")
bl335a = conn.execute("""
    SELECT pt.name as tier, pr.price_usd
    FROM products p
    JOIN prices pr ON pr.product_id = p.rowid
    JOIN price_tiers pt ON pt.id = pr.tier_id
    WHERE p.model='BL335A'
    ORDER BY pt.sort_order
""").fetchall()
for r in bl335a:
    print(f"  {r[0]:25s} = ${r[1]:.2f}")

print(f"\n🎯 Y01:")
y01 = conn.execute("""
    SELECT p.source_file, pt.name as tier, pr.price_usd
    FROM products p
    JOIN prices pr ON pr.product_id = p.rowid
    JOIN price_tiers pt ON pt.id = pr.tier_id
    WHERE p.model='Y01' AND p.source_file LIKE '%ARMxy%'
    ORDER BY pt.sort_order
""").fetchall()
for r in y01:
    print(f"  [{str(r[0])[:45]:45s}] {r[1]:15s} = ${r[2]:.2f}")

conn.close()
print("\nDONE!")
