import xlrd

wb = xlrd.open_workbook(r"C:\Users\Admin\Desktop\Working\1.报价文件\202605 BLIIOT RTU&Router Price List.xls", formatting_info=True)
sh = wb.sheet_by_name("4G Band & Countries")
print("=== 4G Band & Countries ===")
for r in range(sh.nrows):
    vals = [str(sh.cell(r,c).value) for c in range(sh.ncols)]
    sep = " | "
    line = sep.join(vals)
    print("R" + str(r) + ": " + line)
