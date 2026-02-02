import datetime
from collections import defaultdict
from ortools.sat.python import cp_model
from doctor_data import adjust_doctor_data, SHIFT_TIMES, DOCTOR_AUTOPSY_DATA, DOCTOR_NEWYEAREVE_DATA, DOCTOR_NEWYEAR_DATA
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


def generate_schedule_ortools(year, month, doctor_data, time_limit_seconds=300):
    """
    Generate a schedule using OR-Tools CP-SAT solver.
    
    Args:
        year: int, the year for the schedule
        month: int, the month for the schedule
        doctor_data: dict, the doctor availability data
        time_limit_seconds: int, maximum time for solver (default 300 seconds)
    
    Returns:
        schedule: dict mapping date to list of (shift_type, shift_time, doctor)
    """
    doctor_data = adjust_doctor_data(doctor_data)
    days_in_month = (datetime.date(year, month % 12 + 1, 1) - datetime.timedelta(days=1)).day
    days = [datetime.date(year, month, d) for d in range(1, days_in_month + 1)]
    doctors = list(doctor_data.keys())
    
    # Prepare all shifts to assign
    all_shifts = []
    for date in days:
        is_wkend = is_weekend(date) or is_holiday(date)
        shifts = WEEKEND_SHIFTS if is_wkend else WEEKDAY_SHIFTS
        key = "weekend" if is_wkend else "weekday"
        for shift_type, shift_time in shifts:
            all_shifts.append((date, shift_type, shift_time, key))
    
    # Create the model
    model = cp_model.CpModel()
    
    # Create decision variables: shifts[(date, shift_type, shift_time, doctor)] = BoolVar
    shifts = {}
    for date, shift_type, shift_time, key in all_shifts:
        for doctor in doctors:
            var_name = f"shift_d{date.day}_st{shift_type}_t{shift_time}_doc{doctor}"
            shifts[(date, shift_type, shift_time, doctor)] = model.NewBoolVar(var_name)
    
    # Constraint 1: Each shift must be assigned to exactly one doctor
    for date, shift_type, shift_time, key in all_shifts:
        model.Add(sum(shifts[(date, shift_type, shift_time, doctor)] for doctor in doctors) == 1)
    
    # Constraint 2: Each doctor must work exactly their allocated number of shifts per period/type
    for doctor in doctors:
        for period in ["weekday", "weekend"]:
            for shift_type in ["ER", "ward"]:
                expected_shifts = doctor_data[doctor][period][shift_type]
                relevant_shifts = [
                    shifts[(date, st, shift_time, doctor)]
                    for date, st, shift_time, key in all_shifts
                    if key == period and st == shift_type and (date, st, shift_time, doctor) in shifts
                ]
                if relevant_shifts:
                    model.Add(sum(relevant_shifts) == expected_shifts)
    
    # Constraint 3: No doctor can work two different shift types at the same time
    for date in days:
        for shift_time in [SHIFT_TIMES["DAY"], SHIFT_TIMES["EVENING"], SHIFT_TIMES["NIGHT"]]:
            for doctor in doctors:
                # Get all shifts for this doctor at this time
                shift_types_at_time = []
                for shift_type in ["ER", "ward"]:
                    if (date, shift_type, shift_time, doctor) in shifts:
                        shift_types_at_time.append(shifts[(date, shift_type, shift_time, doctor)])
                # At most one shift type per time slot
                if len(shift_types_at_time) > 1:
                    model.Add(sum(shift_types_at_time) <= 1)
    
    # Constraint 4: No more than 2 consecutive shifts per doctor
    # We need to check for consecutive shift patterns
    for doctor in doctors:
        for date in days:
            is_wkday = not (is_weekend(date) or is_holiday(date))
            prev_date = date - datetime.timedelta(days=1)
            next_date = date + datetime.timedelta(days=1)
            
            # Pattern 1: Night shift -> Day shift (forbidden)
            if next_date <= days[-1]:
                if (date, "ER", SHIFT_TIMES["NIGHT"], doctor) in shifts or (date, "ward", SHIFT_TIMES["NIGHT"], doctor) in shifts:
                    night_vars = []
                    if (date, "ER", SHIFT_TIMES["NIGHT"], doctor) in shifts:
                        night_vars.append(shifts[(date, "ER", SHIFT_TIMES["NIGHT"], doctor)])
                    if (date, "ward", SHIFT_TIMES["NIGHT"], doctor) in shifts:
                        night_vars.append(shifts[(date, "ward", SHIFT_TIMES["NIGHT"], doctor)])
                    
                    next_day_vars = []
                    if (next_date, "ER", SHIFT_TIMES["DAY"], doctor) in shifts:
                        next_day_vars.append(shifts[(next_date, "ER", SHIFT_TIMES["DAY"], doctor)])
                    if (next_date, "ward", SHIFT_TIMES["DAY"], doctor) in shifts:
                        next_day_vars.append(shifts[(next_date, "ward", SHIFT_TIMES["DAY"], doctor)])
                    
                    # If works night shift, cannot work day shift next day
                    for night_var in night_vars:
                        for day_var in next_day_vars:
                            model.Add(night_var + day_var <= 1)
            
            # Pattern 2: More than 2 consecutive shifts in a row
            # For weekdays: every doctor already has 1 day shift (08:30-16:30)
            if is_wkday:
                # Since day shift is already taken, can only work evening OR night, not both
                # This prevents: Day + Evening + Night (3 consecutive)
                curr_evening_vars = []
                curr_night_vars = []
                
                if (date, "ER", SHIFT_TIMES["EVENING"], doctor) in shifts:
                    curr_evening_vars.append(shifts[(date, "ER", SHIFT_TIMES["EVENING"], doctor)])
                if (date, "ward", SHIFT_TIMES["EVENING"], doctor) in shifts:
                    curr_evening_vars.append(shifts[(date, "ward", SHIFT_TIMES["EVENING"], doctor)])
                
                if (date, "ER", SHIFT_TIMES["NIGHT"], doctor) in shifts:
                    curr_night_vars.append(shifts[(date, "ER", SHIFT_TIMES["NIGHT"], doctor)])
                if (date, "ward", SHIFT_TIMES["NIGHT"], doctor) in shifts:
                    curr_night_vars.append(shifts[(date, "ward", SHIFT_TIMES["NIGHT"], doctor)])
                
                # At most 1 shift on weekdays (since day shift already counts as 1)
                all_weekday_shifts = curr_evening_vars + curr_night_vars
                if len(all_weekday_shifts) > 1:
                    model.Add(sum(all_weekday_shifts) <= 1)
                
                # Also prevent: Night (prev day) + Day (implicit) + Evening (current day)
                # If worked night previous day, cannot work evening current day
                if prev_date >= days[0] and curr_evening_vars:
                    prev_night_vars = []
                    if (prev_date, "ER", SHIFT_TIMES["NIGHT"], doctor) in shifts:
                        prev_night_vars.append(shifts[(prev_date, "ER", SHIFT_TIMES["NIGHT"], doctor)])
                    if (prev_date, "ward", SHIFT_TIMES["NIGHT"], doctor) in shifts:
                        prev_night_vars.append(shifts[(prev_date, "ward", SHIFT_TIMES["NIGHT"], doctor)])
                    
                    if prev_night_vars:
                        model.Add(sum(prev_night_vars) + sum(curr_evening_vars) <= 1)
                
                # Prevent: Evening (prev day) + Night (prev day) + Day (implicit current day)
                # If worked both evening AND night on previous day, that's already 2 consecutive shifts
                # So cannot have the implicit day shift on current weekday
                if prev_date >= days[0]:
                    prev_evening_vars = []
                    prev_night_vars = []
                    
                    if (prev_date, "ER", SHIFT_TIMES["EVENING"], doctor) in shifts:
                        prev_evening_vars.append(shifts[(prev_date, "ER", SHIFT_TIMES["EVENING"], doctor)])
                    if (prev_date, "ward", SHIFT_TIMES["EVENING"], doctor) in shifts:
                        prev_evening_vars.append(shifts[(prev_date, "ward", SHIFT_TIMES["EVENING"], doctor)])
                    
                    if (prev_date, "ER", SHIFT_TIMES["NIGHT"], doctor) in shifts:
                        prev_night_vars.append(shifts[(prev_date, "ER", SHIFT_TIMES["NIGHT"], doctor)])
                    if (prev_date, "ward", SHIFT_TIMES["NIGHT"], doctor) in shifts:
                        prev_night_vars.append(shifts[(prev_date, "ward", SHIFT_TIMES["NIGHT"], doctor)])
                    
                    # If worked both evening and night on prev day, prevent having current weekday
                    # Since we can't directly forbid "having a weekday", we forbid working evening AND night together on prev day when current is weekday
                    if prev_evening_vars and prev_night_vars:
                        model.Add(sum(prev_evening_vars) + sum(prev_night_vars) <= 1)
            else:
                # Weekend: Check Day -> Evening -> Night
                curr_day_vars = []
                curr_evening_vars = []
                curr_night_vars = []
                
                if (date, "ER", SHIFT_TIMES["DAY"], doctor) in shifts:
                    curr_day_vars.append(shifts[(date, "ER", SHIFT_TIMES["DAY"], doctor)])
                if (date, "ward", SHIFT_TIMES["DAY"], doctor) in shifts:
                    curr_day_vars.append(shifts[(date, "ward", SHIFT_TIMES["DAY"], doctor)])
                
                if (date, "ER", SHIFT_TIMES["EVENING"], doctor) in shifts:
                    curr_evening_vars.append(shifts[(date, "ER", SHIFT_TIMES["EVENING"], doctor)])
                if (date, "ward", SHIFT_TIMES["EVENING"], doctor) in shifts:
                    curr_evening_vars.append(shifts[(date, "ward", SHIFT_TIMES["EVENING"], doctor)])
                
                if (date, "ER", SHIFT_TIMES["NIGHT"], doctor) in shifts:
                    curr_night_vars.append(shifts[(date, "ER", SHIFT_TIMES["NIGHT"], doctor)])
                if (date, "ward", SHIFT_TIMES["NIGHT"], doctor) in shifts:
                    curr_night_vars.append(shifts[(date, "ward", SHIFT_TIMES["NIGHT"], doctor)])
                
                for curr_day_var in curr_day_vars:
                    for curr_evening_var in curr_evening_vars:
                        for curr_night_var in curr_night_vars:
                            model.Add(curr_day_var + curr_evening_var + curr_night_var <= 2)

    # Constraint 5: Autopsy conflicts - doctors cannot work shifts that conflict with autopsy
    for doctor in doctors:
        if doctor in DOCTOR_AUTOPSY_DATA:
            for autopsy_date, autopsy_time in DOCTOR_AUTOPSY_DATA[doctor]:
                # Cannot work the same shift time on autopsy date
                for shift_type in ["ER", "ward"]:
                    if (autopsy_date, shift_type, autopsy_time, doctor) in shifts:
                        model.Add(shifts[(autopsy_date, shift_type, autopsy_time, doctor)] == 0)
                
                # Additional autopsy conflict rules
                # If autopsy at DAY time, cannot work Evening shift (same day)
                if autopsy_time == SHIFT_TIMES["DAY"]:
                    for shift_type in ["ER", "ward"]:
                        if (autopsy_date, shift_type, SHIFT_TIMES["EVENING"], doctor) in shifts:
                            model.Add(shifts[(autopsy_date, shift_type, SHIFT_TIMES["EVENING"], doctor)] == 0)

                # If autopsy at EVENING time, cannot work any shift that day (blocks DAY, EVENING, NIGHT)
                if autopsy_time == SHIFT_TIMES["EVENING"]:
                    for shift_time in [SHIFT_TIMES["DAY"], SHIFT_TIMES["EVENING"], SHIFT_TIMES["NIGHT"]]:
                        for shift_type in ["ER", "ward"]:
                            if (autopsy_date, shift_type, shift_time, doctor) in shifts:
                                model.Add(shifts[(autopsy_date, shift_type, shift_time, doctor)] == 0)
                
                # If autopsy at NIGHT time, cannot work EVENING shift (same day)
                if autopsy_time == SHIFT_TIMES["NIGHT"]:
                    for shift_type in ["ER", "ward"]:
                        if (autopsy_date, shift_type, SHIFT_TIMES["EVENING"], doctor) in shifts:
                            model.Add(shifts[(autopsy_date, shift_type, SHIFT_TIMES["EVENING"], doctor)] == 0)
                
                # Cross-day conflicts
                prev_date = autopsy_date - datetime.timedelta(days=1)
                next_date = autopsy_date + datetime.timedelta(days=1)
                
                # If autopsy DAY on day D, cannot work NIGHT on day D-1
                if autopsy_time == SHIFT_TIMES["DAY"] and prev_date >= days[0]:
                    for shift_type in ["ER", "ward"]:
                        if (prev_date, shift_type, SHIFT_TIMES["NIGHT"], doctor) in shifts:
                            model.Add(shifts[(prev_date, shift_type, SHIFT_TIMES["NIGHT"], doctor)] == 0)
                
                # If autopsy NIGHT on day D, cannot work DAY on day D+1
                if autopsy_time == SHIFT_TIMES["NIGHT"] and next_date <= days[-1]:
                    for shift_type in ["ER", "ward"]:
                        if (next_date, shift_type, SHIFT_TIMES["DAY"], doctor) in shifts:
                            model.Add(shifts[(next_date, shift_type, SHIFT_TIMES["DAY"], doctor)] == 0)
    
    # Constraint 6: New Year Eve shifts - doctors with assigned NYE shifts must work that many shifts on Night Dec 30 and All Dec 31
    nye_date1 = datetime.date(year, 12, 30)
    nye_date2 = datetime.date(year, 12, 31)
    for doctor in doctors:
        if doctor in DOCTOR_NEWYEAREVE_DATA:
            required_nye_shifts = DOCTOR_NEWYEAREVE_DATA[doctor]
            nye_shift_vars = []
            # Night shift on Dec 30
            for shift_type in ["ER", "ward"]:
                if (nye_date1, shift_type, SHIFT_TIMES["NIGHT"], doctor) in shifts:
                    nye_shift_vars.append(shifts[(nye_date1, shift_type, SHIFT_TIMES["NIGHT"], doctor)])
            # All shifts on Dec 31
            for shift_type, shift_time in WEEKEND_SHIFTS:
                if (nye_date2, shift_type, shift_time, doctor) in shifts:
                    nye_shift_vars.append(shifts[(nye_date2, shift_type, shift_time, doctor)])
            if nye_shift_vars:
                model.Add(sum(nye_shift_vars) == required_nye_shifts)
                
    # constraint 7: New Year Day shifts - doctors with assigned NY shifts must work that many shifts on Jan 1-4
    ny_dates = [datetime.date(2026, 1, d) for d in range(1, 5)]
    for doctor in doctors:
        if doctor in DOCTOR_NEWYEAR_DATA:
            required_ny_shifts = DOCTOR_NEWYEAR_DATA[doctor]
            ny_shift_vars = []
            for ny_date in ny_dates:
                is_wkend = is_weekend(ny_date) or is_holiday(ny_date)
                shifts_list = WEEKEND_SHIFTS if is_wkend else WEEKDAY_SHIFTS
                for shift_type, shift_time in shifts_list:
                    if (ny_date, shift_type, shift_time, doctor) in shifts:
                        ny_shift_vars.append(shifts[(ny_date, shift_type, shift_time, doctor)])
            if ny_shift_vars:
                model.Add(sum(ny_shift_vars) == required_ny_shifts)
    
    # Soft constraints: Minimize consecutive shifts with same time on consecutive days
    penalty_vars = []
    for doctor in doctors:
        for i in range(len(days) - 1):
            date = days[i]
            next_date = days[i + 1]
            
            for shift_time in [SHIFT_TIMES["DAY"], SHIFT_TIMES["EVENING"], SHIFT_TIMES["NIGHT"]]:
                # Collect all shifts at this time on current day
                curr_shifts = []
                for shift_type in ["ER", "ward"]:
                    curr_key = (date, shift_type, shift_time, doctor)
                    if curr_key in shifts:
                        curr_shifts.append(shifts[curr_key])
                
                # Collect all shifts at this time on next day
                next_shifts = []
                for shift_type in ["ER", "ward"]:
                    next_key = (next_date, shift_type, shift_time, doctor)
                    if next_key in shifts:
                        next_shifts.append(shifts[next_key])
                
                # If doctor works any shift at this time on both days, add penalty
                if curr_shifts and next_shifts:
                    penalty_var = model.NewBoolVar(f"penalty_{doctor}_d{date.day}_{date.day+1}_t{shift_time}")
                    # penalty_var = 1 iff (any curr_shift) AND (any next_shift)
                    curr_any = model.NewBoolVar(f"curr_any_{doctor}_d{date.day}_t{shift_time}")
                    next_any = model.NewBoolVar(f"next_any_{doctor}_d{date.day+1}_t{shift_time}")
                    model.AddMaxEquality(curr_any, curr_shifts)
                    model.AddMaxEquality(next_any, next_shifts)
                    model.AddMultiplicationEquality(penalty_var, [curr_any, next_any])
                    penalty_vars.append(penalty_var)
    
    # Minimize the total penalty
    if penalty_vars:
        model.Minimize(sum(penalty_vars))

    # Create the solver and solve
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = time_limit_seconds
    solver.parameters.log_search_progress = True
    
    print("[OR-Tools CP-SAT] Solving...")
    status = solver.Solve(model)
    
    if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
        print(f"[OR-Tools CP-SAT] Solution found with status: {solver.StatusName(status)}")
        print(f"[OR-Tools CP-SAT] Wall time: {solver.WallTime():.2f}s")
        
        # Extract the solution
        schedule = defaultdict(list)
        for date, shift_type, shift_time, key in all_shifts:
            for doctor in doctors:
                if (date, shift_type, shift_time, doctor) in shifts:
                    if solver.Value(shifts[(date, shift_type, shift_time, doctor)]) == 1:
                        schedule[date].append((shift_type, shift_time, doctor))
                        break
        
        return dict(schedule)
    else:
        print(f"[OR-Tools CP-SAT] No solution found. Status: {solver.StatusName(status)}")
        print("[OR-Tools CP-SAT] Falling back to empty schedule.")
        return {}


def generate_schedule(year, month, doctor_data, max_iter=100000, initial_temp=10.0, cooling_rate=0.995):
    """
    Wrapper function that uses OR-Tools CP-SAT solver.
    The signature matches the original simulated annealing function for compatibility.
    
    Args:
        year: int
        month: int
        doctor_data: dict
        max_iter: int (unused, kept for API compatibility)
        initial_temp: float (unused, kept for API compatibility)
        cooling_rate: float (unused, kept for API compatibility)
    
    Returns:
        schedule: dict mapping date to list of (shift_type, shift_time, doctor)
    """
    return generate_schedule_ortools(year, month, doctor_data, time_limit_seconds=300)
