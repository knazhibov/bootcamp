#!/usr/bin/env python3
"""Запуск аналитических запросов поверх Parquet-таблиц."""

from __future__ import annotations

import argparse

from pyspark.sql import SparkSession

from config import OUTPUT_PATH


def create_spark_session() -> SparkSession:
    return SparkSession.builder.appName("SparkifyAnalytics").getOrCreate()


def load_tables(spark: SparkSession, output_path):
    return {
        name: spark.read.parquet(str(output_path / name))
        for name in ("artists", "songs", "users", "time_table", "songplays")
    }


def register_views(tables: dict) -> None:
    for name, df in tables.items():
        df.createOrReplaceTempView(name)


def run_analytics(spark: SparkSession, output_path=OUTPUT_PATH) -> None:
    tables = load_tables(spark, output_path)
    register_views(tables)

    print("=== Самый популярный трек по дням ===")
    spark.sql(
        """
        SELECT
            DATE(sp.start_time) AS play_day,
            s.title,
            a.name AS artist_name,
            COUNT(*) AS play_count
        FROM songplays sp
        JOIN songs s ON sp.song_id = s.song_id
        JOIN artists a ON sp.artist_id = a.artist_id
        GROUP BY play_day, s.title, a.name
        """
    ).createOrReplaceTempView("daily_plays")

    spark.sql(
        """
        SELECT play_day, title, artist_name, play_count
        FROM (
            SELECT *,
                   ROW_NUMBER() OVER (PARTITION BY play_day ORDER BY play_count DESC) AS rn
            FROM daily_plays
        ) ranked
        WHERE rn = 1
        ORDER BY play_day
        """
    ).show(truncate=False)

    print("=== Самые часто прослушиваемые треки ===")
    spark.sql(
        """
        SELECT
            s.title,
            a.name AS artist_name,
            COUNT(*) AS total_plays
        FROM songplays sp
        JOIN songs s ON sp.song_id = s.song_id
        JOIN artists a ON sp.artist_id = a.artist_id
        GROUP BY s.title, a.name
        ORDER BY total_plays DESC
        """
    ).show(truncate=False)

    print("=== Самые популярные треки за неделю ===")
    spark.sql(
        """
        SELECT week, year, title, artist_name, weekly_plays
        FROM (
            SELECT
                t.week,
                t.year,
                s.title,
                a.name AS artist_name,
                COUNT(*) AS weekly_plays,
                ROW_NUMBER() OVER (PARTITION BY t.week, t.year ORDER BY COUNT(*) DESC) AS rn
            FROM songplays sp
            JOIN time_table t ON sp.start_time = t.start_time
            JOIN songs s ON sp.song_id = s.song_id
            JOIN artists a ON sp.artist_id = a.artist_id
            GROUP BY t.week, t.year, s.title, a.name
        ) ranked
        WHERE rn = 1
        ORDER BY year, week
        """
    ).show(truncate=False)

    print("=== Самые популярные треки за месяц ===")
    spark.sql(
        """
        SELECT month, year, title, artist_name, monthly_plays
        FROM (
            SELECT
                t.month,
                t.year,
                s.title,
                a.name AS artist_name,
                COUNT(*) AS monthly_plays,
                ROW_NUMBER() OVER (PARTITION BY t.month, t.year ORDER BY COUNT(*) DESC) AS rn
            FROM songplays sp
            JOIN time_table t ON sp.start_time = t.start_time
            JOIN songs s ON sp.song_id = s.song_id
            JOIN artists a ON sp.artist_id = a.artist_id
            GROUP BY t.month, t.year, s.title, a.name
        ) ranked
        WHERE rn = 1
        ORDER BY year, month
        """
    ).show(truncate=False)


def parse_args():
    parser = argparse.ArgumentParser(description="Sparkify analytics")
    parser.add_argument("--output", type=str, default=str(OUTPUT_PATH))
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    spark = create_spark_session()
    try:
        run_analytics(spark, args.output)
    finally:
        spark.stop()
