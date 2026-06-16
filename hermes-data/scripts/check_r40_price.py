import xlrd

wb = xlrd.open_workbook(r"C:\Users\Admin\Desktop\Working\1.报价文件\202605 BLIIOT RTU&Router Price List.xls", formatting_info=True)
sh = wb.sheet_by_index(0)
print(f"Sheet: {sh.name} ({sh.nrows}x{sh.ncols})")

# Header row (row 5)
cols = [str(sh.cell(5,c).value) for c in range(sh.ncols)]
print(f"HEADER: {' | '.join(cols)}")
print()

print("=== R40 PRICES ===")
for r in range(6, sh.nrows):
    r0 = str(sh.cell(r,0).value).upper()
    r3 = str(sh.cell(r,3).value).upper()
    if "R40" in r0 or "R40" in r3:
        vals = [str(sh.cell(r,c).value) for c in range(sh.ncols)]
        print(f"Row {r}: {' | '.join(vals)}")
