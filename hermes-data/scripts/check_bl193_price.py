import xlrd

files = [
    r"C:\Users\Admin\Desktop\Working\1.报价文件\202605 BLIIOT IOy Series Edge IO Module Price List.xls",
    r"C:\Users\Admin\Desktop\Working\1.报价文件\202511 IOy Series Edge IO Module Price List.xls",
]

for fpath in files:
    print(f"\n=== Reading: {fpath.split(chr(92))[-1]} ===")
    try:
        wb = xlrd.open_workbook(fpath, formatting_info=True)
        for si in range(wb.nsheets):
            sh = wb.sheet_by_index(si)
            print(f"  Sheet: {sh.name} ({sh.nrows}x{sh.ncols})")
            # Print header
            for r in range(min(10, sh.nrows)):
                vals = [str(sh.cell(r,c).value) for c in range(sh.ncols)]
                line = " | ".join(vals)
                if any(x in line.upper() for x in ["BL193", "Y11", "Y31", "MODEL", "NAME", "PRICE", "QTY"]):
                    print(f"  Row {r}: {line}")
                elif r < 4:
                    print(f"  Row {r}: {line}")
            # Search for BL193 rows
            print(f"\n  --- BL193/Y11/Y31 rows ---")
            for r in range(10, sh.nrows):
                vals = [str(sh.cell(r,c).value) for c in range(sh.ncols)]
                line = " | ".join(vals)
                if "BL193" in line.upper() or "Y11" in line.upper() or "Y31" in line.upper():
                    print(f"  Row {r}: {line}")
    except Exception as e:
        print(f"  Error: {e}")
