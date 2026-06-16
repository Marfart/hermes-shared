import xlrd

fpath = r"C:\Users\Admin\Desktop\Working\1.报价文件\202605 BLIIOT IOy Series Edge IO Module Price List.xls"
wb = xlrd.open_workbook(fpath, formatting_info=True)
sh = wb.sheet_by_index(0)

print(f"=== Full sheet: {sh.nrows}x{sh.ncols} ===")
for r in range(sh.nrows):
    vals = [str(sh.cell(r,c).value) for c in range(sh.ncols)]
    line = " | ".join(vals)
    print(f"R{r}: {line}")
