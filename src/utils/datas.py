from datetime import datetime


def br_to_iso(date_str: str) -> str:
    return datetime.strptime(date_str, "%d/%m/%Y").date().isoformat()


def iso_to_br(date_str: str) -> str:
    return datetime.strptime(date_str, "%Y-%m-%d").strftime("%d/%m/%Y")
