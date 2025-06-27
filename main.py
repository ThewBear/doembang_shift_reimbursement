from doctor_data import DOCTOR_DATA
from scheduler import (
    generate_schedule,
    print_expected_shifts,
    print_schedule_summary,
    print_schedule,
    verify_schedule,
    verify_total_shifts_against_doctor_data
)
from excel_export import save_schedule_to_xlsx

if __name__ == "__main__":
    year = 2025
    month = 6
    if verify_total_shifts_against_doctor_data(year, month, DOCTOR_DATA):
        print_expected_shifts(DOCTOR_DATA)
        schedule = generate_schedule(year, month, DOCTOR_DATA)
        print_schedule_summary(schedule)
        print_schedule(schedule)
        verify_schedule(schedule, DOCTOR_DATA)
        save_schedule_to_xlsx(schedule)
