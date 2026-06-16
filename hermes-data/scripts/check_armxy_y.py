import xlrd

# Check 202512 ARMxy file for Y board pricing (since Y board is dual-column in ARMxy file)
fpath = r"C:\Users\Admin\Desktop\Working\1.报价文件\202512 ARMxy Series Embedded Computer Price List.xlsx"
try:
    wb = xlrd.open_workbook(fpath)
    print(f"Sheets: {wb.sheet_names()}")
    for si in range(wb.nsheets):
        sh = wb.sheet_by_index(si)
        print(f"\n=== Sheet: {sh.name} ({sh.nrows}x{sh.ncols}) ===")
        for r in range(sh.nrows):
            vals = [str(sh.cell(r,c).value) for c in range(sh.ncols)]
            line = " | ".join(vals)
            if any(x in line.upper() for x in ["Y11", "Y31", "BL193", "Y板", "MODEL", "PRICE", "QTY", "SAMPLE"]):
                print(f"R{r}: {line}")
            elif r < 8:
                print(f"R{r}: {line}")
except Exception as e:
    print(f"Error reading {fpath}: {e}")
