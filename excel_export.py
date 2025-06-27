import pandas as pd
import os
from doctor_data import DOCTOR_DATA, adjust_doctor_data
from constraints import is_weekend, is_holiday

def save_schedule_to_xlsx(schedule, filename="schedule.xlsx"):
    all_shifts = set()
    for date in schedule:
        for shift_type, shift_time, _ in schedule[date]:
            all_shifts.add((shift_type, shift_time))
    all_shifts = sorted(all_shifts, key=lambda x: (x[0], x[1]))
    data = []
    dates = sorted(schedule.keys())
    for date in dates:
        row = {f"{stype} {stime}": "" for stype, stime in all_shifts}
        for shift_type, shift_time, doctor in schedule[date]:
            row[f"{shift_type} {shift_time}"] = doctor
        row = {
            "Period": "Weekend" if is_weekend(date) or is_holiday(date) else "Weekday",
            "Day": date.strftime("%A")
        } | row
        data.append(row)
    df = pd.DataFrame(data, index=dates)
    df.index.name = "Date"
    with pd.ExcelWriter(filename, engine="openpyxl") as writer:
        df.to_excel(writer, sheet_name="Schedule")
        ws = writer.sheets["Schedule"]
        start_col = len(df.columns) + 2
        for row in range(1, len(df) + 2):
            ws.cell(row=row, column=start_col-1, value=None)
        doctors = list(DOCTOR_DATA.keys())
        ws.cell(row=1, column=start_col, value="Doctor")
        ws.cell(row=1, column=start_col+1, value="Weekday ER")
        ws.cell(row=1, column=start_col+2, value="Weekday ward")
        ws.cell(row=1, column=start_col+3, value="Weekend ER")
        ws.cell(row=1, column=start_col+4, value="Weekend ward")
        for i, doctor in enumerate(doctors):
            row_num = i + 2
            ws.cell(row=row_num, column=start_col, value=doctor)
            col_map = {col: idx+2 for idx, col in enumerate(df.columns)}
            for j, (period, shift_type) in enumerate([
                ("weekday", "ER"), ("weekday", "ward"), ("weekend", "ER"), ("weekend", "ward")]):
                count_formula = []
                for r, date in enumerate(dates):
                    is_wkend = is_weekend(date) or is_holiday(date)
                    if (period == "weekend" and is_wkend) or (period == "weekday" and not is_wkend):
                        for col in df.columns:
                            if col.startswith(shift_type):
                                cell = ws.cell(row=r+2, column=col_map[col]).coordinate
                                count_formula.append(f'--({cell}="{doctor}")')
                if count_formula:
                    formula = f'=SUM({" ".join(count_formula)})'
                else:
                    formula = '=0'
                ws.cell(row=row_num, column=start_col+1+j, value=formula)
        expected_row = len(doctors) + 3
        ws.cell(row=expected_row-1, column=start_col, value="Expected")
        ws.cell(row=expected_row, column=start_col, value="Doctor")
        ws.cell(row=expected_row, column=start_col+1, value="Weekday ER")
        ws.cell(row=expected_row, column=start_col+2, value="Weekday ward")
        ws.cell(row=expected_row, column=start_col+3, value="Weekend ER")
        ws.cell(row=expected_row, column=start_col+4, value="Weekend ward")
        adjusted = adjust_doctor_data(DOCTOR_DATA)
        for i, doctor in enumerate(doctors):
            ws.cell(row=expected_row+1+i, column=start_col, value=doctor)
            ws.cell(row=expected_row+1+i, column=start_col+1, value=adjusted[doctor]["weekday"]["ER"])
            ws.cell(row=expected_row+1+i, column=start_col+2, value=adjusted[doctor]["weekday"]["ward"])
            ws.cell(row=expected_row+1+i, column=start_col+3, value=adjusted[doctor]["weekend"]["ER"])
            ws.cell(row=expected_row+1+i, column=start_col+4, value=adjusted[doctor]["weekend"]["ward"])
        from openpyxl.styles import PatternFill
        light_orange = PatternFill(start_color="FFF8CBAD", end_color="FFF8CBAD", fill_type="solid")
        light_green = PatternFill(start_color="FFD9EAD3", end_color="FFD9EAD3", fill_type="solid")
        schedule_col_count = len(df.columns)
        for idx, date in enumerate(dates):
            excel_row = idx + 2
            period = ws.cell(row=excel_row, column=2).value
            fill = light_orange if period == "Weekend" else light_green
            for col in range(1, schedule_col_count + 1):
                ws.cell(row=excel_row, column=col).fill = fill
    print(f"Schedule saved to {os.path.abspath(filename)}")
