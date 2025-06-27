import datetime
from doctor_data import THAI_HOLIDAYS

def is_weekend(date):
    return date.weekday() >= 5

def is_holiday(date):
    return date in THAI_HOLIDAYS

def violates_constraints(schedule, doctor, date, shift_type, shift_time):
    # No double booking in ER and ward at the same time
    for s_type, s_time, d in schedule[date]:
        if d == doctor:
            if s_time == shift_time:
                return True
    # No continuous shift between 16.30-00.30 and 00.30-08.30 of the next day
    if shift_time == "16.30-00.30":
        next_day = date + datetime.timedelta(days=1)
        if next_day in schedule:
            for s_type, s_time, d in schedule[next_day]:
                if d == doctor and s_time == "00.30-08.30":
                    return True
    if shift_time == "00.30-08.30":
        prev_day = date - datetime.timedelta(days=1)
        if prev_day in schedule:
            for s_type, s_time, d in schedule[prev_day]:
                if d == doctor and s_time == "16.30-00.30":
                    return True
    # No continuous shift between 00.30-08.30 and 08.30-16.30
    if shift_time == "08.30-16.30":
        for s_type, s_time, d in schedule[date]:
            if d == doctor and s_time == "00.30-08.30":
                return True
    if shift_time == "00.30-08.30":
        for s_type, s_time, d in schedule[date]:
            if d == doctor and s_time == "08.30-16.30":
                return True
    # On weekday, no 00.30-08.30 and 16.30-00.30 on same day
    if not is_weekend(date):
        if shift_time in ["00.30-08.30", "16.30-00.30"]:
            for s_type, s_time, d in schedule[date]:
                if d == doctor and s_time in ["00.30-08.30", "16.30-00.30"] and s_time != shift_time:
                    return True
    return False
