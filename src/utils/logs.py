import logging
from pathlib import Path


def get_logger(name: str) -> logging.Logger:
    Path("logs").mkdir(exist_ok=True)

    logger = logging.getLogger(name)
    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        datefmt="%d/%m/%Y %H:%M:%S",
    )

    file_handler = logging.FileHandler("logs/radar_pescados_ia.log", encoding="utf-8")
    file_handler.setFormatter(formatter)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger
