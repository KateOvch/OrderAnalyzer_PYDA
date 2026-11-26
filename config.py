# -*- coding: utf-8 -*-

"""
Настройки проекта пакетного анализа заказов.
Все пути и параметры фильтрации вынесены сюда.
"""
from pathlib import Path

# Корневая директория проекта (папка, где лежит config.py)
BASE_DIR = Path(__file__).resolve().parent

# Папки проекта
DATA_DIR = BASE_DIR / "data"
REPORTS_DIR = BASE_DIR / "reports"
LOGS_DIR = BASE_DIR / "logs"

# Имя итогового отчёта
SUMMARY_REPORT_NAME = "summary_report.csv"

# Имя лог-файла ошибок
ERROR_LOG_NAME = "errors.log"

# Параметры бизнес-логики
STATUS_COLUMN = "status"
DELIVERED_STATUS = "Delivered"
AMOUNT_COLUMN = "total_amount"

# Колонки, которые обязаны присутствовать во входном файле
REQUIRED_COLUMNS = [
    "order_id",
    "person_id",
    "order_date",
    "status",
    "total_amount",
    "currency",
    "payment_method",
    "shipping_method",
    "notes",
]
