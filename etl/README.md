# ETL для музыкального сервиса Сбер

Проект загружает JSON-данные активности пользователей и метаданные песен,
формирует звёздную схему и сохраняет таблицы в Parquet (аналог HDFS).

## Архитектура

```
JSON (song_data) ──► artists, songs
JSON (log_data)  ──► users, time_table, songplays
```

### Таблицы

| Таблица | Тип | Описание |
|---------|-----|----------|
| `artists` | dimension | Исполнители |
| `songs` | dimension | Песни (FK → artists) |
| `users` | dimension | Пользователи |
| `time_table` | dimension | Временные атрибуты |
| `songplays` | fact | Лог прослушиваний (FK → users, songs, artists, time_table) |

## Структура проекта

```
sparkify_etl/
├── data/
│   ├── song_data/     # JSON с метаданными песен
│   └── log_data/      # JSON с активностью пользователей
├── sql/
│   ├── create_tables.sql
│   ├── analytics.sql
│   └── test_queries.sql
├── config.py
├── etl.py             # Основной ETL-пайплайн
├── analytics.py       # Аналитические запросы
└── output/            # Parquet-таблицы (локальный аналог HDFS)
```

## Установка

```bash
cd projects/sparkify_etl
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Требуется Java 8+ для PySpark.

## Запуск ETL

```bash
python etl.py
```

С кастомными путями:

```bash
python etl.py \
  --song-data data/song_data \
  --log-data data/log_data \
  --output output
```

В продакшене замените `--output` на HDFS-путь, например:
`hdfs:///user/sparkify/dwh`

## Аналитика

```bash
python analytics.py
```

Или SQL-запросы из `sql/analytics.sql` после загрузки в PostgreSQL/Redshift.

## DDL для реляционной БД

```bash
psql -d sparkify -f sql/create_tables.sql
```

## Формат входных данных

**song_data** — метаданные песен:
- `song_id`, `title`, `artist_id`, `artist_name`, `duration`, `year`

**log_data** — активность пользователей:
- `userId`, `firstName`, `lastName`, `gender`, `level`
- `sessionId`, `location`, `userAgent`, `page`, `ts`
- `song`, `artist`, `length` (для событий `NextSong`)

## Дополнительные задачи

Реализованы в `analytics.py` и `sql/analytics.sql`:

1. Самый популярный трек по дням
2. Самые часто прослушиваемые треки
3. Самые популярные треки за неделю / месяц
