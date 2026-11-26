# -*- coding: utf-8 -*-
python
"""
Точка входа: запускает пакетный анализ заказов.
Запуск: python run.py
"""
import config
from src.analyzer import OrderAnalyzer


def main() -> None:
    analyzer = OrderAnalyzer(
        data_dir=config.DATA_DIR,
        reports_dir=config.REPORTS_DIR,
        logs_dir=config.LOGS_DIR,
    )
    report_path = analyzer.process_all_files()

    print("\n===== ИТОГИ =====")
    print(f"Успешно обработано файлов: {analyzer.processed_files}")
    print(f"Файлов с ошибками:         {analyzer.failed_files}")
    print(f"Отчёт:                     {report_path}")
    if analyzer.failed_files:
        print(
            f"Подробности в логе:        "
            f"{config.LOGS_DIR / config.ERROR_LOG_NAME}"
        )


if __name__ == "__main__":
    main()