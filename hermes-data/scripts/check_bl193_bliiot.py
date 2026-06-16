import xlrd

# Check the BLIIoT Price List for BL193
wb = xlrd.open_workbook(r"C:\Users\Admin\Desktop\Working\1.报价文件\BLIIoT Price List 20240527.xls", formatting_info=True)
for si in range(wb.nsheets):
    sh = wb.sheet_by_index(si)
    print(f"Sheet: {sh.name} ({sh.nrows}x{sh.ncols})")
    for r in range(sh.nrows):
        vals = [str(sh.cell(r,c).value) for c in range(sh.ncols)]
        line = " | ".join(vals)
        if "BL193" in line.upper() or "Y11" in line.upper() or "Y31" in line.upper():
            print(f"R{r}: {line}")
        elif r < 10:
            print(f"R{r}: {line}")
