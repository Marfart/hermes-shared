import xlrd

files = [
    r"C:\Users\Admin\Desktop\Working\1.报价文件\202605 BLIIOT RTU&Router Price List.xls",
    r"C:\Users\Admin\Desktop\Working\1.报价文件\BLIIoT Price List 20240527.xls",
    r"C:\Users\Admin\Desktop\Working\1.报价文件\202605 BLIIOT IIoT Gateways &BL116&BL118 Price List.xls",
    r"C:\Users\Admin\Desktop\Working\1.报价文件\202512 IIoT Gateways Price List.xls",
    r"C:\Users\Admin\Desktop\Working\1.报价文件\BLIIoT BL16 Series Industrial Ethernet Switch Price List.xls",
    r"C:\Users\Admin\Desktop\Working\1.报价文件\202605 BLIIOT IOy Series Edge IO Module Price List.xls",
    r"C:\Users\Admin\Desktop\Working\1.报价文件\202511 IOy Series Edge IO Module Price List.xls",
]

for fpath in files:
    try:
        wb = xlrd.open_workbook(fpath, formatting_info=True)
        sh = wb.sheet_by_index(0)
    except:
        continue
    
    found = False
    for r in range(sh.nrows):
        for c in range(sh.ncols):
            val = str(sh.cell(r,c).value).strip()
            if "S130" in val.upper():
                if not found:
                    print(f"\n=== {fpath.split(chr(92))[-1]} ===")
                    found = True
                vals = [str(sh.cell(r,c2).value) for c2 in range(sh.ncols)]
                print(f"R{r}: {' | '.join(vals)}")
    if found:
        # Print header rows for context
        sh2 = wb.sheet_by_index(0)
        for r2 in range(min(10, sh2.nrows)):
            vals2 = [str(sh2.cell(r2,c).value) for c in range(sh2.ncols)]
            line = " | ".join(vals2)
            if any(x in line.upper() for x in ["S130", "MODEL", "NAME", "PRICE", "QTY", "SAMPLE", "<100"]):
                print(f"  H{r2}: {line}")
