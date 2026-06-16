import xlrd

fpath = r"C:\Users\Admin\Desktop\Working\1.报价文件\202605 BLIIOT RTU&Router Price List.xls"
wb = xlrd.open_workbook(fpath, formatting_info=True)
sh = wb.sheet_by_index(0)

print("=== S130 - ALL ROWS ===")
for r in range(sh.nrows):
    r0 = str(sh.cell(r,0).value).strip()
    if r0.upper() == "S130" or r0.upper().startswith("S130"):
        vals = [str(sh.cell(r,c).value) for c in range(sh.ncols)]
        print(f"R{r}: {' | '.join(vals)}")
        # Also show next row if it's a continuation (same model, different version)
        if r+1 < sh.nrows:
            next_r0 = str(sh.cell(r+1,0).value).strip()
            if next_r0 == "":
                r2 = r+1
                while r2 < sh.nrows and str(sh.cell(r2,0).value).strip() == "":
                    vals2 = [str(sh.cell(r2,c).value) for c in range(sh.ncols)]
                    non_empty = [v for v in vals2 if v.strip()]
                    if len(non_empty) > 0 and "S130" not in str(sh.cell(r2,3).value).upper():
                        break
                    print(f"R{r2}: {' | '.join(vals2)}")
                    r2 += 1

print("\n\n=== Also scanning for S130 near row 136-145 ===")
for r in range(125, 150):
    vals = [str(sh.cell(r,c).value) for c in range(sh.ncols)]
    line = " | ".join(vals)
    non_empty = [v for v in vals if v.strip()]
    if len(non_empty) > 0:
        print(f"R{r}: {line[:300]}")
