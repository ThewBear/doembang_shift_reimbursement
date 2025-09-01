# Shift Reimbursement Scheduler

This project generates a monthly doctor shift schedule and exports it to Excel, including summary tables and color-coded rows for easy review.

## Features
- Generates ER and ward shifts for doctors, respecting constraints and holidays.
- Outputs an Excel file with:
  - Daily schedule
  - Per-doctor shift summary (actual vs expected)
  - Color-coded rows for weekends and weekdays
- Verifies that all shifts are assigned and match expected counts.

## Usage
1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Generate a schedule:
   ```bash
   python main.py
   ```
   The output Excel file (`schedule.xlsx`) will be created in the project directory.

3. Generate a blank schedule template (for manual entry):
   ```bash
   python main.py blank --year 2025 --month 7
   ```
   The output Excel file (`blank_schedule.xlsx`) will be created in the project directory.

## Requirements
- Python 3.8+
- See `requirements.txt` for Python package dependencies.

## Customization
- Edit `DOCTOR_DATA` and `THAI_HOLIDAYS` in `generate_schedule.py` to match your needs.

## Output Example
- `schedule.xlsx` contains the schedule, summary, and expected shift counts.
