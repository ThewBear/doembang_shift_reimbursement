import copy
import datetime
import random
from collections import defaultdict
from doctor_data import adjust_doctor_data, SHIFT_TIMES
from constraints import is_weekend, is_holiday, violates_constraints

WEEKDAY_SHIFTS = [
    ("ER", SHIFT_TIMES["EVENING"]),
    ("ER", SHIFT_TIMES["NIGHT"]),
    ("ward", SHIFT_TIMES["EVENING"])
]
WEEKEND_SHIFTS = [
    ("ER", SHIFT_TIMES["DAY"]),
    ("ER", SHIFT_TIMES["EVENING"]),
    ("ER", SHIFT_TIMES["NIGHT"]),
    ("ward", SHIFT_TIMES["DAY"]),
    ("ward", SHIFT_TIMES["EVENING"]),
    ("ward", SHIFT_TIMES["NIGHT"])
]

def generate_schedule(year, month, doctor_data, max_iter=100000, initial_temp=10.0, cooling_rate=0.995):
    """
    Generate a schedule using simulated annealing.
    Args:
        year, month: int
        doctor_data: dict
        max_iter: int, number of iterations
        initial_temp: float, starting temperature
        cooling_rate: float, temperature decay per iteration
    Returns:
        schedule: dict mapping date to list of (shift_type, shift_time, doctor)
    """
    doctor_data = adjust_doctor_data(doctor_data)
    days_in_month = (datetime.date(year, month % 12 + 1, 1) - datetime.timedelta(days=1)).day
    days = [datetime.date(year, month, d) for d in range(1, days_in_month+1)]
    doctors = list(doctor_data.keys())

    # Use a local random instance for reproducibility
    local_random = random.Random()
    local_random.seed(42)

    # Prepare all shifts to assign: list of (date, shift_type, shift_time, period_key)
    all_shifts = []
    for date in days:
        is_wkend = is_weekend(date) or is_holiday(date)
        shifts = WEEKEND_SHIFTS if is_wkend else WEEKDAY_SHIFTS
        key = "weekend" if is_wkend else "weekday"
        for shift_type, shift_time in shifts:
            all_shifts.append((date, shift_type, shift_time, key))

    def get_initial_remaining():
        return {
            doctor: {period: sum(types.values()) for period, types in doctor_data[doctor].items()}
            for doctor in doctor_data
        }

    def random_schedule():
        schedule = defaultdict(list)
        remaining = get_initial_remaining()
        for date, shift_type, shift_time, key in all_shifts:
            possible_doctors = [doctor for doctor in doctors if remaining[doctor][key] > 0 and not violates_constraints(schedule, doctor, date, shift_type, shift_time)]
            if possible_doctors:
                doctor = local_random.choice(possible_doctors)
                schedule[date].append((shift_type, shift_time, doctor))
                remaining[doctor][key] -= 1
            else:
                fallback_doctors = [doctor for doctor in doctors if remaining[doctor][key] > 0]
                if fallback_doctors:
                    doctor = local_random.choice(fallback_doctors)
                    schedule[date].append((shift_type, shift_time, doctor))
                    remaining[doctor][key] -= 1
                else:
                    raise RuntimeError(f"No doctors with remaining quota for {date} {shift_type} {shift_time} ({key}). Please verify doctor_data.")
        return schedule, 0

    def cost(schedule):
        return sum(
            1
            for date in schedule
            for shift_type, shift_time, doctor in schedule[date]
            if violates_constraints(schedule, doctor, date, shift_type, shift_time)
        )

    def neighbor(schedule):
        new_schedule = copy.deepcopy(schedule)
        def get_period(date):
            return "weekend" if is_weekend(date) or is_holiday(date) else "weekday"
        assigned_by_period = {"weekday": [], "weekend": []}
        for date in new_schedule:
            period = get_period(date)
            for idx, s in enumerate(new_schedule[date]):
                assigned_by_period[period].append((date, idx, s))
        periods_with_enough = [p for p in assigned_by_period if len(assigned_by_period[p]) >= 2]
        if not periods_with_enough:
            return new_schedule
        period = local_random.choice(periods_with_enough)
        (date1, idx1, (shift_type1, shift_time1, doctor1)), (date2, idx2, (shift_type2, shift_time2, doctor2)) = local_random.sample(assigned_by_period[period], 2)
        new_schedule[date1][idx1] = (shift_type1, shift_time1, doctor2)
        new_schedule[date2][idx2] = (shift_type2, shift_time2, doctor1)
        return new_schedule

    current_schedule, _ = random_schedule()
    current_cost = cost(current_schedule)
    best_schedule = copy.deepcopy(current_schedule)
    best_cost = current_cost
    temp = initial_temp
    for iteration in range(max_iter):
        new_schedule = neighbor(current_schedule)
        new_cost = cost(new_schedule)
        delta = new_cost - current_cost
        if delta < 0 or local_random.random() < (2.71828 ** (-delta / temp)):
            current_schedule = new_schedule
            current_cost = new_cost
            if new_cost < best_cost:
                best_schedule = copy.deepcopy(new_schedule)
                best_cost = new_cost
        temp *= cooling_rate
        if best_cost == 0:
            print(f"[Simulated Annealing] Found best cost 0 after {iteration} iterations.")
            break
    print(f"[Simulated Annealing] Best cost: {best_cost}")
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
        wd_er = adjusted[doctor]["weekday"]["ER"]
        wd_ward = adjusted[doctor]["weekday"]["ward"]
        we_er = adjusted[doctor]["weekend"]["ER"]
        we_ward = adjusted[doctor]["weekend"]["ward"]
        wd_total = wd_er + wd_ward
        we_total = we_er + we_ward
        print(f"Doctor: {doctor} | weekday ER: {wd_er}, ward: {wd_ward}, total: {wd_total} | weekend ER: {we_er}, ward: {we_ward}, total: {we_total}")
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
            print(f"    {period} total: {summary[doctor][period]['ER'] + summary[doctor][period]['ward']}")
    print()

def verify_schedule(schedule, doctor_data):
    adjusted = adjust_doctor_data(doctor_data)
    # Track total shifts per doctor per period (ignore ER/ward distinction)
    summary = {doctor: {"weekday": 0, "weekend": 0} for doctor in adjusted}
    unassigned_count = 0
    for date in schedule:
        period = "weekend" if is_weekend(date) or is_holiday(date) else "weekday"
        for shift_type, shift_time, doctor in schedule[date]:
            if doctor == "Unassigned":
                unassigned_count += 1
            else:
                summary[doctor][period] += 1
    if unassigned_count > 0:
        print(f"ERROR: There are {unassigned_count} unassigned shifts!")
    else:
        print("All shifts are assigned.")
    all_match = True
    for doctor in adjusted:
        for period in ["weekday", "weekend"]:
            expected = adjusted[doctor][period]["ER"] + adjusted[doctor][period]["ward"]
            actual = summary[doctor][period]
            if expected != actual:
                print(f"ERROR: {doctor} {period}: expected {expected}, got {actual}")
                all_match = False
    if all_match and unassigned_count == 0:
        print("Schedule verification PASSED: All counts match and no unassigned shifts.")
    elif all_match:
        print("Schedule verification WARNING: All counts match but there are unassigned shifts.")
    else:
        print("Schedule verification FAILED: See errors above.")

def verify_total_shifts_against_doctor_data(year, month, doctor_data):
    num_days = (datetime.date(year, month % 12 + 1, 1) - datetime.timedelta(days=1)).day
    days = [datetime.date(year, month, d) for d in range(1, num_days+1)]
    total = {"weekday": 0, "weekend": 0}
    for date in days:
        is_wkend = is_weekend(date) or is_holiday(date)
        if is_wkend:
            total["weekend"] += 6  # 3 ER + 3 ward
        else:
            total["weekday"] += 3  # 2 ER + 1 ward
    adjusted = adjust_doctor_data(doctor_data)
    sum_doctors = {"weekday": 0, "weekend": 0}
    for doctor in adjusted:
        for period in ["weekday", "weekend"]:
            for shift_type in ["ER", "ward"]:
                sum_doctors[period] += adjusted[doctor][period][shift_type]
    print("Verifying total shifts in month against doctor_data (ER+ward combined)...")
    all_match = True
    for period in ["weekday", "weekend"]:
        expected = total[period]
        actual = sum_doctors[period]
        print(f"{period}: schedule slots = {expected}, doctor_data total = {actual}")
        if expected != actual:
            print(f"ERROR: {period} mismatch!")
            all_match = False
    if all_match:
        print("Total shifts match doctor_data. Proceeding to generate schedule.\n")
    else:
        print("ERROR: Total shifts do not match doctor_data. Please check your input.\n")
    return all_match
