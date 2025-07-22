import datetime

DOCTOR_DATA = {
    "ธนัท": {
        "weekday": {"ER": 5, "ward": 4},
        "weekend": {"ER": 3, "ward": 3}
    },
    "กุลประวีณ์": {
        "weekday": {"ER": 4, "ward": 5},
        "weekend": {"ER": 3, "ward": 3}
    },
    "สุประวีณ์": {
        "weekday": {"ER": 5, "ward": 5},
        "weekend": {"ER": 2, "ward": 3}
    },
    "กุลพักตร์": {
        "weekday": {"ER": 5, "ward": 5},
        "weekend": {"ER": 3, "ward": 2}
    },
}

THAI_HOLIDAYS = [
    # June
    datetime.date(2025, 6, 2),   # Visakha Bucha Day
    datetime.date(2025, 6, 3),   # Queen Suthida's Birthday
    
    # July
    datetime.date(2025, 7, 28),  # King Vajiralongkorn's Birthday
    datetime.date(2025, 7, 30),  # Asalha Bucha Day
    
    # August
    datetime.date(2025, 8, 11),  # Bridge Public Holiday
    datetime.date(2025, 8, 12),  # The Queen's Birthday (Queen Mother's Day)
    
    # October
    datetime.date(2025, 10, 13), # Anniversary of the Death of King Bhumibol
    datetime.date(2025, 10, 23), # Chulalongkorn Day
    
    # December
    datetime.date(2025, 12, 5),  # King Bhumibol's Birthday/Father's Day
    datetime.date(2025, 12, 10), # Constitution Day
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
