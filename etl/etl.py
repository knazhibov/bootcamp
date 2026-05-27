#!/usr/bin/env python3
"""
ETL-пайплайн для музыкального сервиса Сбер.

Обрабатывает JSON-логи активности и метаданные песен,
формирует звёздную схему и сохраняет таблицы в Parquet (HDFS).
"""

from __future__ import annotations

import argparse
from pathlib import Path

from pyspark.sql import SparkSession
from pyspark.sql.functions import col, expr, monotonically_increasing_id, to_timestamp

from config import LOG_DATA_PATH, OUTPUT_PATH, SONG_DATA_PATH, TABLES


def create_spark_session(app_name: str = "SparkifyETL") -> SparkSession:
    return (
        SparkSession.builder.appName(app_name)
        .config("spark.sql.parquet.writeLegacyFormat", "true")
        .getOrCreate()
    )


def process_song_metadata(spark: SparkSession, input_path: Path):
    """Извлекает dimension-таблицы artists и songs из song_data."""
    df = spark.read.json(str(input_path))

    artists_df = (
        df.select(
            col("artist_id"),
            col("artist_name").alias("name"),
            col("artist_location").alias("location"),
            col("artist_latitude").alias("latitude"),
            col("artist_longitude").alias("longitude"),
        )
        .dropDuplicates(["artist_id"])
    )

    songs_df = (
        df.select(
            col("song_id"),
            col("title"),
            col("artist_id"),
            col("year"),
            col("duration"),
        )
        .dropDuplicates(["song_id"])
    )

    return artists_df, songs_df


def process_log_data(spark: SparkSession, input_path: Path):
    """Извлекает dimension-таблицы users и time_table из log_data."""
    df = spark.read.json(str(input_path))

    users_df = (
        df.filter(col("page") == "NextSong")
        .select(
            col("userId").alias("user_id"),
            col("firstName").alias("first_name"),
            col("lastName").alias("last_name"),
            col("gender"),
            col("level"),
        )
        .dropDuplicates(["user_id"])
    )

    time_df = (
        df.filter(col("page") == "NextSong")
        .select(
            to_timestamp(col("ts") / 1000).alias("start_time"),
            expr("hour(from_unixtime(ts / 1000))").alias("hour"),
            expr("day(from_unixtime(ts / 1000))").alias("day"),
            expr("weekofyear(from_unixtime(ts / 1000))").alias("week"),
            expr("month(from_unixtime(ts / 1000))").alias("month"),
            expr("year(from_unixtime(ts / 1000))").alias("year"),
            expr("dayofweek(from_unixtime(ts / 1000))").alias("weekday"),
        )
        .dropDuplicates(["start_time"])
    )

    return users_df, time_df


def process_songplays(spark: SparkSession, log_path: Path, song_path: Path):
    """Формирует fact-таблицу songplays через join логов и метаданных."""
    log_df = spark.read.json(str(log_path))
    song_df = spark.read.json(str(song_path))

    songplays_df = (
        log_df.filter(col("page") == "NextSong")
        .join(
            song_df,
            (log_df.song == song_df.title) & (log_df.artist == song_df.artist_name),
            "inner",
        )
        .select(
            to_timestamp(col("ts") / 1000).alias("start_time"),
            col("userId").alias("user_id"),
            col("level"),
            col("sessionId").alias("session_id"),
            col("location"),
            col("userAgent").alias("user_agent"),
            col("song_id"),
            col("artist_id"),
        )
        .withColumn("songplay_id", monotonically_increasing_id())
    )

    return songplays_df


def save_table(df, output_path: Path, table_name: str, mode: str = "overwrite") -> None:
    target = output_path / table_name
    df.write.mode(mode).parquet(str(target))
    print(f"Saved {table_name}: {df.count()} rows -> {target}")


def run_etl(
    song_data_path: Path = SONG_DATA_PATH,
    log_data_path: Path = LOG_DATA_PATH,
    output_path: Path = OUTPUT_PATH,
) -> None:
    spark = create_spark_session()

    try:
        print("Processing song metadata...")
        artists_df, songs_df = process_song_metadata(spark, song_data_path)

        print("Processing user activity logs...")
        users_df, time_df = process_log_data(spark, log_data_path)

        print("Building songplays fact table...")
        songplays_df = process_songplays(spark, log_data_path, song_data_path)

        output_path.mkdir(parents=True, exist_ok=True)

        save_table(artists_df, output_path, "artists")
        save_table(songs_df, output_path, "songs")
        save_table(users_df, output_path, "users")
        save_table(time_df, output_path, "time_table")
        save_table(songplays_df, output_path, "songplays")

        print("\nETL completed successfully.")
        print(f"Output tables: {', '.join(TABLES)}")
        print(f"Location: {output_path}")
    finally:
        spark.stop()


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Sparkify ETL pipeline")
    parser.add_argument(
        "--song-data",
        type=Path,
        default=SONG_DATA_PATH,
        help="Path to song metadata JSON files",
    )
    parser.add_argument(
        "--log-data",
        type=Path,
        default=LOG_DATA_PATH,
        help="Path to user activity log JSON files",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=OUTPUT_PATH,
        help="Output path (local HDFS analog)",
    )
    return parser.parse_args(argv)


if __name__ == "__main__":
    args = parse_args()
    run_etl(args.song_data, args.log_data, args.output)
