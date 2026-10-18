def seat_exists(seat: str, pattern: str) -> bool:
    """Проверяет, что место есть в схеме площадки.

    seat_exists("B15", "A1-1000,B1-2000") -> True
    seat_exists("C1", "A1-1000,B1-2000") -> False
    """
    section, number = seat[0], seat[1:]
    if not number.isdigit():
        return False
    for part in pattern.split(","):
        start, end = part.split("-")
        if section == start[0] and int(start[1:]) <= int(number) <= int(end):
            return True
    return False
