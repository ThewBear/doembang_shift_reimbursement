import datetime
import random
from collections import defaultdict
import concurrent.futures
from doctor_data import adjust_doctor_data
from constraints import is_weekend, is_holiday, violates_constraints

WEEKDAY_SHIFTS = [
    ("ER", "16.30-00.30"),
    ("ER", "00.30-08.30"),
    ("ward", "16.30-00.30")
]
WEEKEND_SHIFTS = [
    ("ER", "08.30-16.30"),
    ("ER", "16.30-00.30"),
    ("ER", "00.30-08.30"),
    ("ward", "08.30-16.30"),
    ("ward", "16.30-00.30"),
    ("ward", "00.30-08.30")
]

def generate_schedule(year, month, doctor_data, max_retries=100000, num_threads=8):
    doctor_data = adjust_doctor_data(doctor_data)
    days_in_month = (datetime.date(year, month % 12 + 1, 1) - datetime.timedelta(days=1)).day
    days = [datetime.date(year, month, d) for d in range(1, days_in_month+1)]
    doctors = list(doctor_data.keys())

    def try_generate(seed):
        schedule = defaultdict(list)
        remaining = {d: {k: v.copy() for k, v in doctor_data[d].items()} for d in doctor_data}
        rnd = random.Random(seed)
        for date in days:
            is_wkend = is_weekend(date) or is_holiday(date)
            shifts = WEEKEND_SHIFTS if is_wkend else WEEKDAY_SHIFTS
            for shift_type, shift_time in shifts:
                assigned = False
                rnd.shuffle(doctors)
                key = "weekend" if is_wkend else "weekday"
                for doctor in doctors:
                    if remaining[doctor][key][shift_type] > 0:
                        if not violates_constraints(schedule, doctor, date, shift_type, shift_time):
                            schedule[date].append((shift_type, shift_time, doctor))
                            remaining[doctor][key][shift_type] -= 1
                            assigned = True
                            break
                if not assigned:
                    schedule[date].append((shift_type, shift_time, "Unassigned"))
        unassigned = sum(
            doctor == "Unassigned"
            for date in schedule for _, _, doctor in schedule[date]
        )
        return (unassigned, schedule)

    seeds = [42 + i for i in range(max_retries)]
    best_unassigned = float('inf')
    best_schedule = None
    with concurrent.futures.ThreadPoolExecutor(max_workers=num_threads) as executor:
        futures = [executor.submit(try_generate, seed) for seed in seeds]
        for future in concurrent.futures.as_completed(futures):
            unassigned, schedule = future.result()
            if unassigned < best_unassigned:
                best_unassigned = unassigned
                best_schedule = schedule
            if unassigned == 0:
                return schedule
    return best_schedule

def print_schedule(schedule):
    for date in sorted(schedule.keys()):
        print(f"{date}:")
        for shift_type, shift_time, doctor in schedule[date]:
            print(f"  {shift_type} {shift_time}: {doctor}")
        print()

def print_expected_shifts(doctor_data):
    adjusted = adjust_doctor_data(doctor_data)
    print("Expected 8-hour shifts per doctor:")
    for doctor in adjusted:
        print(f"Doctor: {doctor}")
        for period in ["weekday", "weekend"]:
            for shift_type in ["ER", "ward"]:
                print(f"  {period} {shift_type}: {adjusted[doctor][period][shift_type]}")
    print()

def print_schedule_summary(schedule):
    summary = {}
    for date in schedule:
        period = "weekend" if is_weekend(date) or is_holiday(date) else "weekday"
        for shift_type, shift_time, doctor in schedule[date]:
            if doctor == "Unassigned":
                continue
            if doctor not in summary:
                summary[doctor] = {"weekday": {"ER": 0, "ward": 0}, "weekend": {"ER": 0, "ward": 0}}
            summary[doctor][period][shift_type] += 1
    print("Generated 8-hour shifts per doctor:")
    for doctor in summary:
        print(f"Doctor: {doctor}")
        for period in ["weekday", "weekend"]:
            for shift_type in ["ER", "ward"]:
                print(f"  {period} {shift_type}: {summary[doctor][period][shift_type]}")
    print()

def verify_schedule(schedule, doctor_data):
    from doctor_data import adjust_doctor_data
    adjusted = adjust_doctor_data(doctor_data)
    summary = {doctor: {"weekday": {"ER": 0, "ward": 0}, "weekend": {"ER": 0, "ward": 0}} for doctor in adjusted}
    unassigned_count = 0
    for date in schedule:
        period = "weekend" if is_weekend(date) or is_holiday(date) else "weekday"
        for shift_type, shift_time, doctor in schedule[date]:
            if doctor == "Unassigned":
                unassigned_count += 1
            else:
                summary[doctor][period][shift_type] += 1
    if unassigned_count > 0:
        print(f"ERROR: There are {unassigned_count} unassigned shifts!")
    else:
        print("All shifts are assigned.")
    all_match = True
    for doctor in adjusted:
        for period in ["weekday", "weekend"]:
            for shift_type in ["ER", "ward"]:
                expected = adjusted[doctor][period][shift_type]
                actual = summary[doctor][period][shift_type]
                if expected != actual:
                    print(f"ERROR: {doctor} {period} {shift_type}: expected {expected}, got {actual}")
                    all_match = False
    if all_match and unassigned_count == 0:
        print("Schedule verification PASSED: All counts match and no unassigned shifts.")
    elif all_match:
        print("Schedule verification WARNING: All counts match but there are unassigned shifts.")
    else:
        print("Schedule verification FAILED: See errors above.")

def verify_total_shifts_against_doctor_data(year, month, doctor_data):
    from doctor_data import adjust_doctor_data
    num_days = (datetime.date(year, month % 12 + 1, 1) - datetime.timedelta(days=1)).day
    days = [datetime.date(year, month, d) for d in range(1, num_days+1)]
    total = {"weekday": {"ER": 0, "ward": 0}, "weekend": {"ER": 0, "ward": 0}}
    for date in days:
        is_wkend = is_weekend(date) or is_holiday(date)
        if is_wkend:
            total["weekend"]["ER"] += 3
            total["weekend"]["ward"] += 3
        else:
            total["weekday"]["ER"] += 2
            total["weekday"]["ward"] += 1
    adjusted = adjust_doctor_data(doctor_data)
    sum_doctors = {"weekday": {"ER": 0, "ward": 0}, "weekend": {"ER": 0, "ward": 0}}
    for doctor in adjusted:
        for period in ["weekday", "weekend"]:
            for shift_type in ["ER", "ward"]:
                sum_doctors[period][shift_type] += adjusted[doctor][period][shift_type]
    print("Verifying total shifts in month against doctor_data...")
    all_match = True
    for period in ["weekday", "weekend"]:
        for shift_type in ["ER", "ward"]:
            expected = total[period][shift_type]
            actual = sum_doctors[period][shift_type]
            print(f"{period} {shift_type}: schedule slots = {expected}, doctor_data total = {actual}")
            if expected != actual:
                print(f"ERROR: {period} {shift_type} mismatch!")
                all_match = False
    if all_match:
        print("Total shifts match doctor_data. Proceeding to generate schedule.\n")
    else:
        print("ERROR: Total shifts do not match doctor_data. Please check your input.\n")
    return all_match
