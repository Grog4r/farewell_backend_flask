from datetime import date


def calculate_unlock_date(creation_date, leave_date):
    unlock_date = date(day=creation_date.day, month=creation_date.month, year=2023)
    if unlock_date < leave_date:
        unlock_date = date(day=creation_date.day, month=creation_date.month, year=2024)
    return unlock_date
