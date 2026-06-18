import xlrd

wb = xlrd.open_workbook(r'C:\Users\Admin\Desktop\出货\报价数据\202511 ARMxy Series BL360 Embedded Computer Price List.xls')
for sheet_name in wb.sheet_names():
    ws = wb.sheet_by_name(sheet_name)
    print(f'=== Sheet: {sheet_name} ({ws.nrows} rows x {ws.ncols} cols) ===')
    for r in range(min(ws.nrows, 80)):
        row = []
        for c in range(ws.ncols):
            cell = ws.cell(r, c)
            row.append(str(cell.value))
        print(f'  R{r}: {" | ".join(row)}')
    print()