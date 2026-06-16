import xlrd

wb = xlrd.open_workbook(r"C:\Users\Admin\Desktop\Working\1.报价文件\202605 BLIIOT RTU&Router Price List.xls", formatting_info=True)
sh = wb.sheet_by_index(0)

# Check formatting for the price cells to determine rounding
xf = wb.xf_list

print("=== ALL R40 ROWS ===")
for r in range(6, 23):
    r0 = str(sh.cell(r,0).value).upper()
    # Show all rows near R40 section
    vals = [str(sh.cell(r,c).value) for c in range(sh.ncols)]
    print(f"Row {r}: {' | '.join(vals)}")
    print()
