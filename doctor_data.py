import datetime

SHIFT_TIMES = {
    "DAY": "08.30-16.30",
    "EVENING": "16.30-00.30",
    "NIGHT": "00.30-08.30",
}

BLANK_DOCTOR_LIST = [
    "ธนัท",
    "กุลประวีณ์",
    "สุประวีณ์",
    "กุลพักตร์",
    "พัชรพร",
    "กรภัทร์"
]

DOCTOR_DATA = {
    "ธนัท": {
        "weekday": {"ER": 3, "ward": 4},
        "weekend": {"ER": 2, "ward": 1},
    },
    "กุลประวีณ์": {
        "weekday": {"ER": 3, "ward": 4},
        "weekend": {"ER": 2, "ward": 2}
    },
    "สุประวีณ์": {
        "weekday": {"ER": 4, "ward": 3},
        "weekend": {"ER": 1, "ward": 3}
    },
    "กุลพักตร์": {
        "weekday": {"ER": 4, "ward": 3},
        "weekend": {"ER": 2, "ward": 1}
    },
    "พัชรพร": {
        "weekday": {"ER": 3, "ward": 3},
        "weekend": {"ER": 2, "ward": 2}
    },
    "กรภัทร์": {
        "weekday": {"ER": 3, "ward": 3},
        "weekend": {"ER": 2, "ward": 2}
    },
}

DOCTOR_NEWYEAREVE_DATA = {
    "ธนัท": 2,
    "กุลประวีณ์": 2,
    "สุประวีณ์": 2,
    "กุลพักตร์": 0,
    "พัชรพร": 0,
    "กรภัทร์": 1,
}

DOCTOR_NEWYEAR_DATA = {
    "ธนัท": 7-DOCTOR_NEWYEAREVE_DATA["ธนัท"],
    "กุลประวีณ์": 6-DOCTOR_NEWYEAREVE_DATA["กุลประวีณ์"],
    "สุประวีณ์": 6-DOCTOR_NEWYEAREVE_DATA["สุประวีณ์"],
    "กุลพักตร์": 3-DOCTOR_NEWYEAREVE_DATA["กุลพักตร์"],
    "พัชรพร": 3-DOCTOR_NEWYEAREVE_DATA["พัชรพร"],
    "กรภัทร์": 6-DOCTOR_NEWYEAREVE_DATA["กรภัทร์"],
}

DOCTOR_AUTOPSY_DATA = {
    "ธนัท": [
        (datetime.date(2026, 1, 23), SHIFT_TIMES["EVENING"]),
    ],
    "กุลประวีณ์": [
        (datetime.date(2026, 1, 7), SHIFT_TIMES["EVENING"]),
    ],
    "สุประวีณ์": [
    ],
    "กุลพักตร์": [
    ],
    "พัชรพร": [
        (datetime.date(2026, 1, 12), SHIFT_TIMES["NIGHT"]),
        (datetime.date(2026, 1, 28), SHIFT_TIMES["EVENING"]),
    ],
    "กรภัทร์": []
}

THAI_HOLIDAYS = [
    # December
    datetime.date(2025, 12, 5),  # King Bhumibol's Birthday/Father's Day
    datetime.date(2025, 12, 10),  # Constitution Day
    datetime.date(2025, 12, 31),  # New Year's Eve
    
    # January
    datetime.date(2026, 1, 1),   # New Year's Day
    datetime.date(2026, 1, 2),  # Extra New Year Holiday
    
    # --- March 2026 ---
    datetime.date(2026, 3, 3),   # Makha Bucha Day

    # --- April 2026 ---
    datetime.date(2026, 4, 6),   # Chakri Memorial Day
    datetime.date(2026, 4, 13),  # Songkran Festival
    datetime.date(2026, 4, 14),  # Songkran Festival
    datetime.date(2026, 4, 15),  # Songkran Festival

    # --- May 2026 ---
    datetime.date(2026, 5, 4),   # Coronation Day
    datetime.date(2026, 5, 31),  # Visakha Bucha Day
]


def adjust_doctor_data(doctor_data):
    """
    Adjusts doctor shift data by applying specific multipliers to ER and ward shifts.
    For each doctor in the input dictionary:
    - If the doctor has no shift data (empty dictionary), they are skipped.
    - Weekday ER shifts are doubled.
    - Weekend ER and ward shifts are tripled.
    - Weekday ward shifts remain unchanged.
    Args:
        doctor_data (dict): A dictionary where each key is a doctor's name and each value is a dictionary with
            'weekday' and 'weekend' keys, each containing 'ER' and 'ward' shift counts.
    Returns:
        dict: A dictionary with the same structure as the input, but with adjusted shift counts.
    """
    adjusted = {}
    for doctor, data in doctor_data.items():
        # Skip doctors with no shift data (empty dictionary)
        if not data:
            continue
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
