import datetime

DOCTOR_DATA = {
    "Thew": {
        "weekday": {"ER": 5, "ward": 4},
        "weekend": {"ER": 3, "ward": 3}
    },
    "Oum": {
        "weekday": {"ER": 4, "ward": 5},
        "weekend": {"ER": 3, "ward": 3}
    },
    "Parn": {
        "weekday": {"ER": 5, "ward": 5},
        "weekend": {"ER": 2, "ward": 3}
    },
    "Best": {
        "weekday": {"ER": 5, "ward": 5},
        "weekend": {"ER": 3, "ward": 2}
    }
}

THAI_HOLIDAYS = [
    datetime.date(2024, 1, 1),
    datetime.date(2024, 1, 2),
    datetime.date(2024, 2, 26),
    datetime.date(2024, 4, 8),
    datetime.date(2024, 4, 12),
    datetime.date(2024, 4, 15),
    datetime.date(2024, 4, 16),
    datetime.date(2024, 5, 1),
    datetime.date(2024, 5, 6),
    datetime.date(2024, 5, 22),
    datetime.date(2024, 6, 3),
    datetime.date(2024, 7, 22),
    datetime.date(2024, 7, 29),
    datetime.date(2024, 8, 12),
    datetime.date(2024, 10, 14),
    datetime.date(2024, 10, 23),
    datetime.date(2024, 12, 5),
    datetime.date(2024, 12, 10),
    datetime.date(2024, 12, 31)
]

def adjust_doctor_data(doctor_data):
    adjusted = {}
    for doctor, data in doctor_data.items():
        adjusted[doctor] = {
            "weekday": {
                "ER": data["weekday"]["ER"] * 2,
                "ward": data["weekday"]["ward"]
            },
            "weekend": {
                "ER": data["weekend"]["ER"] * 3,
                "ward": data["weekend"]["ward"] * 3
            }
        }
    return adjusted
