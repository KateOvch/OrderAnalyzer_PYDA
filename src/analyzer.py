# -*- coding: utf-8 -*-

"""
Класс OrderAnalyzer: чтение, фильтрация, расчёт метрик и пакетная
обработка CSV-файлов с заказами. Ошибки логируются, но не прерывают
обработку остальных файлов.

Совместимость: Python 3.8+.
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd

import config


class OrderAnalyzer:
    """Анализирует CSV-файлы с заказами и собирает сводные метрики."""

    def __init__(self, data_dir: Path, reports_dir: Path, logs_dir: Path) -> None:
        self.data_dir = Path(data_dir)
        self.reports_dir = Path(reports_dir)
        self.logs_dir = Path(logs_dir)

        # Создаём папки, если их нет
        self.reports_dir.mkdir(parents=True, exist_ok=True)
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        if not self.data_dir.exists():
            self.data_dir.mkdir(parents=True, exist_ok=True)

        # Настраиваем логгер ошибок
        self.logger = logging.getLogger("OrderAnalyzer")
        self.logger.setLevel(logging.ERROR)
        # Чтобы не дублировать хендлеры при повторном создании экземпляра
        if not self.logger.handlers:
            handler = logging.FileHandler(
                self.logs_dir / config.ERROR_LOG_NAME, encoding="utf-8"
            )
            formatter = logging.Formatter(
                "%(asctime)s | %(levelname)s | %(message)s"
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)

        # Счётчики для итогового вывода
        self.processed_files = 0
        self.failed_files = 0

    # ------------------------------------------------------------------
    # Загрузка и валидация
    # ------------------------------------------------------------------
    def load_file(self, file_path: Path) -> pd.DataFrame:
        """
        Загружает CSV-файл и проверяет его структуру.
        Бросает исключение при любой проблеме — вызывающий код его ловит.
        """
        df = pd.read_csv(file_path)

        if df.empty:
            raise ValueError("Файл пуст (нет строк данных)")

        missing = [c for c in config.REQUIRED_COLUMNS if c not in df.columns]
        if missing:
            raise ValueError(f"Отсутствуют обязательные колонки: {missing}")

        # Проверяем, что total_amount приводится к числу
        try:
            df[config.AMOUNT_COLUMN] = pd.to_numeric(
                df[config.AMOUNT_COLUMN], errors="raise"
            )
        except (ValueError, TypeError) as exc:
            raise ValueError(
                f"Колонка '{config.AMOUNT_COLUMN}' содержит нечисловые "
                f"или пустые значения: {exc}"
            )

        return df

    # ------------------------------------------------------------------
    # Бизнес-логика
    # ------------------------------------------------------------------
    def filter_delivered(self, df: pd.DataFrame) -> pd.DataFrame:
        """Оставляет только заказы со статусом Delivered."""
        return df[df[config.STATUS_COLUMN] == config.DELIVERED_STATUS]

    def calculate_metrics(self, df_delivered: pd.DataFrame) -> Dict[str, Any]:
        """Считает выручку, средний чек и количество заказов."""
        orders_count = int(len(df_delivered))
        if orders_count == 0:
            return {
                "orders_count": 0,
                "total_revenue": 0.0,
                "average_order_value": 0.0,
            }

        total_revenue = float(df_delivered[config.AMOUNT_COLUMN].sum())
        avg_order_value = float(df_delivered[config.AMOUNT_COLUMN].mean())

        return {
            "orders_count": orders_count,
            "total_revenue": round(total_revenue, 2),
            "average_order_value": round(avg_order_value, 2),
        }

    # ------------------------------------------------------------------
    # Обработка одного файла и всех файлов
    # ------------------------------------------------------------------
    def process_file(self, file_path: Path) -> Optional[Dict[str, Any]]:
        """
        Обрабатывает один файл. Возвращает словарь с метриками
        или None, если файл не удалось обработать (ошибка залогирована).
        """
        try:
            df = self.load_file(file_path)
            delivered = self.filter_delivered(df)
            metrics = self.calculate_metrics(delivered)

            result = {"file_name": file_path.name, **metrics}
            self.processed_files += 1
            return result

        except Exception as exc:  # noqa: BLE001 — ловим всё, чтобы не упасть
            self.failed_files += 1
            self.logger.error(
                "Ошибка обработки файла '%s': %s", file_path.name, exc
            )
            return None

    def process_all_files(self) -> Path:
        """
        Находит все CSV в data/, обрабатывает их по очереди
        и сохраняет сводный отчёт в reports/. Возвращает путь к отчёту.
        """
        csv_files: List[Path] = sorted(self.data_dir.glob("*.csv"))
        report_path = self.reports_dir / config.SUMMARY_REPORT_NAME

        if not csv_files:
            self.logger.error(
                "В папке '%s' не найдено CSV-файлов", self.data_dir
            )
            print(f"В папке '{self.data_dir}' не найдено CSV-файлов.")
            # Создаём пустой отчёт с заголовками, чтобы файл существовал
            pd.DataFrame(
                columns=[
                    "file_name",
                    "orders_count",
                    "total_revenue",
                    "average_order_value",
                ]
            ).to_csv(report_path, index=False, encoding="utf-8")
            print(f"Создан пустой отчёт: {report_path}")
            return report_path

        results: List[Dict[str, Any]] = []
        for file_path in csv_files:
            print(f"Обработка: {file_path.name} ...")
            result = self.process_file(file_path)
            if result is not None:
                results.append(result)

        if results:
            report_df = pd.DataFrame(
                results,
                columns=[
                    "file_name",
                    "orders_count",
                    "total_revenue",
                    "average_order_value",
                ],
            )
        else:
            # Ни одного успешного файла — всё равно создаём отчёт с заголовками
            report_df = pd.DataFrame(
                columns=[
                    "file_name",
                    "orders_count",
                    "total_revenue",
                    "average_order_value",
                ]
            )

        report_df.to_csv(report_path, index=False, encoding="utf-8")
        print(f"\nОтчёт сохранён: {report_path}")

        return report_path
