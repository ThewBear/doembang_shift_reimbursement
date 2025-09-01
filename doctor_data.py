import datetime

SHIFT_TIMES = {
    "NIGHT": "00.30-08.30",
    "DAY": "08.30-16.30",
    "EVENING": "16.30-00.30",
}

DOCTOR_DATA = {
    "ธนัท": {
        "weekday": {"ER": 4, "ward": 4},
        "weekend": {"ER": 3, "ward": 2},
    },
    "กุลประวีณ์": {
        "weekday": {"ER": 4, "ward": 4},
        "weekend": {"ER": 2, "ward": 3}
    },
    "สุประวีณ์": {
        "weekday": {"ER": 3, "ward": 4},
        "weekend": {"ER": 2, "ward": 3}
    },
    "กุลพักตร์": {
        "weekday": {"ER": 4, "ward": 3},
        "weekend": {"ER": 3, "ward": 2}
    },
    "พัชรพร": {},
    "ชาญวิทย์": {
        "weekday": {"ER": 4, "ward": 4},
        "weekend": {"ER": 2, "ward": 2}
    },
}

DOCTOR_AUTOPSY_DATA = {
    "ธนัท": [],
    "กุลประวีณ์": [
        (datetime.date(2025, 8, 10), SHIFT_TIMES["NIGHT"]),
    ],
    "สุประวีณ์": [
        (datetime.date(2025, 8, 11), SHIFT_TIMES["DAY"]),
        (datetime.date(2025, 8, 12), SHIFT_TIMES["EVENING"])
    ],
    "กุลพักตร์": [
        (datetime.date(2025, 8, 30), SHIFT_TIMES["DAY"])
    ],
    "ชาญวิทย์": [
        (datetime.date(2025, 8, 19), SHIFT_TIMES["EVENING"])
    ]
}

THAI_HOLIDAYS = [
    # June
    datetime.date(2025, 6, 2),   # Visakha Bucha Day
    datetime.date(2025, 6, 3),   # Queen Suthida's Birthday

    # July
    datetime.date(2025, 7, 10),  # Asalha Bucha Day
    datetime.date(2025, 7, 11),  # Beginning of Vassa
    datetime.date(2025, 7, 28),  # King Vajiralongkorn's Birthday

    # August
    datetime.date(2025, 8, 11),  # Bridge Public Holiday
    datetime.date(2025, 8, 12),  # The Queen's Birthday (Queen Mother's Day)

    # October
    datetime.date(2025, 10, 13),  # Anniversary of the Death of King Bhumibol
    datetime.date(2025, 10, 23),  # Chulalongkorn Day

    # December
    datetime.date(2025, 12, 5),  # King Bhumibol's Birthday/Father's Day
    datetime.date(2025, 12, 10),  # Constitution Day
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
