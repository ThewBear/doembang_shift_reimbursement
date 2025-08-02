import datetime
from doctor_data import THAI_HOLIDAYS, SHIFT_TIMES, DOCTOR_AUTOPSY_DATA

def is_weekend(date):
    return date.weekday() >= 5

def is_holiday(date):
    return date in THAI_HOLIDAYS

def is_weekday(date):
    return not is_weekend(date) and not is_holiday(date)

def violates_constraints(schedule, doctor, date, shift_type, shift_time):
    # No double booking in ER and ward at the same time, unless it's the same shift type (current shift)
    for s_type, s_time, d in schedule[date]:
        if d == doctor and s_time == shift_time:
            # Allow if it's the current shift (same type and time)
            if s_type != shift_type:
                return True
    # No more than 2 consecutive shifts for a doctor
    prev_date = date - datetime.timedelta(days=1)
    next_date = date + datetime.timedelta(days=1)
    consecutive_count = 1
    if shift_time == SHIFT_TIMES["DAY"]:
        for s_type, s_time, d in schedule.get(date, []):
            if d == doctor and s_time != SHIFT_TIMES["DAY"]:
                consecutive_count += 1
    if shift_time == SHIFT_TIMES["EVENING"]:
        if is_weekday(date):
            consecutive_count += 1
            for s_type, s_time, d in schedule.get(date, []):
                if d == doctor and s_time == SHIFT_TIMES["NIGHT"]:
                    consecutive_count += 1
        else:
            for s_type, s_time, d in schedule.get(date, []):
                if d == doctor and s_time == SHIFT_TIMES["DAY"]:
                    consecutive_count += 1
        for s_type, s_time, d in schedule.get(next_date, []):
            if d == doctor and s_time == SHIFT_TIMES["NIGHT"]:
                consecutive_count += 1
    if shift_time == SHIFT_TIMES["NIGHT"]:
        for s_type, s_time, d in schedule.get(prev_date, []):
            if d == doctor and s_time == SHIFT_TIMES["EVENING"]:
                consecutive_count += 1
        if is_weekday(date):
            consecutive_count += 1
            for s_type, s_time, d in schedule.get(date, []):
                if d == doctor and s_time == SHIFT_TIMES["EVENING"]:
                    consecutive_count += 1
        else:
            for s_type, s_time, d in schedule.get(date, []):
                if d == doctor and s_time == SHIFT_TIMES["DAY"]:
                    consecutive_count += 1
    if consecutive_count > 2:
        return True
        
    # The shift date and time cannot match the autopsy data
    if doctor in DOCTOR_AUTOPSY_DATA:
        for autopsy_date, autopsy_time in DOCTOR_AUTOPSY_DATA[doctor]:
            if autopsy_date == date and autopsy_time == shift_time:
                return True
    return False
