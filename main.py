import datetime
import argparse
from doctor_data import DOCTOR_DATA
from scheduler import (
    generate_schedule,
    print_expected_shifts,
    print_schedule_summary,
    verify_schedule,
    verify_total_shifts_against_doctor_data
)
from excel_export import save_schedule_to_xlsx
from blank_excel import generate_blank_excel


def main():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command")

    # Blank subcommand
    blank_parser = subparsers.add_parser("blank", help="Generate blank schedule excel file")
    blank_parser.add_argument("--year", type=int, default=datetime.date.today().year)
    blank_parser.add_argument("--month", type=int, default=datetime.date.today().month)

    # Default (generate schedule)
    parser.add_argument("--year", type=int, default=datetime.date.today().year)
    parser.add_argument("--month", type=int, default=datetime.date.today().month)

    args = parser.parse_args()

    if args.command == "blank":
        generate_blank_excel(args.year, args.month)
        return

    year = args.year
    month = args.month
    if verify_total_shifts_against_doctor_data(year, month, DOCTOR_DATA):
        print_expected_shifts(DOCTOR_DATA)
        schedule = generate_schedule(year, month, DOCTOR_DATA)
        print_schedule_summary(schedule)
        verify_schedule(schedule, DOCTOR_DATA)
        save_schedule_to_xlsx(schedule)


if __name__ == "__main__":
    main()
