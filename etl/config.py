"""Конфигурация путей для ETL-пайплайна."""

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent

# Источники JSON-данных
SONG_DATA_PATH = PROJECT_ROOT / "data" / "song_data"
LOG_DATA_PATH = PROJECT_ROOT / "data" / "log_data"

# Локальный аналог HDFS (в проде: hdfs:///user/sparkify/dwh)
OUTPUT_PATH = PROJECT_ROOT / "output"

# Таблицы звёздной схемы
TABLES = ("artists", "songs", "users", "time_table", "songplays")
