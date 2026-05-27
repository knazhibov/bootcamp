#!/usr/bin/env python3
"""Функции визуализации данных музыкального сервиса на Seaborn."""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

from config import LOG_DATA_PATH, OUTPUT_PATH, PLOTS_PATH, PROJECT_ROOT
SEABORN_STYLE = "whitegrid"
SEABORN_PALETTE = "deep"


def setup_style() -> None:
    sns.set_theme(style=SEABORN_STYLE, palette=SEABORN_PALETTE)
    plt.rcParams["figure.figsize"] = (10, 6)
    plt.rcParams["font.size"] = 11


def load_songplays_from_parquet(output_path: Path = OUTPUT_PATH) -> pd.DataFrame:
    """Загружает fact-таблицу и dimension-таблицы из Parquet после ETL."""
    songplays = pd.read_parquet(output_path / "songplays")
    songs = pd.read_parquet(output_path / "songs")
    artists = pd.read_parquet(output_path / "artists")
    users = pd.read_parquet(output_path / "users")
    time_table = pd.read_parquet(output_path / "time_table")

    df = (
        songplays.merge(songs, on="song_id", suffixes=("", "_song"))
        .merge(artists, on="artist_id", suffixes=("", "_artist"))
        .merge(users, on="user_id", suffixes=("", "_user"))
        .merge(time_table, on="start_time", suffixes=("", "_time"))
    )
    df["start_time"] = pd.to_datetime(df["start_time"])
    df["play_day"] = df["start_time"].dt.date
    df["track"] = df["title"] + " — " + df["name"]
    return df


def load_songplays_from_json(log_path: Path = LOG_DATA_PATH) -> pd.DataFrame:
    """Загружает события NextSong из JSON, если ETL ещё не запускали."""
    logs = pd.read_json(log_path / "*.json", lines=True)
    plays = logs[logs["page"] == "NextSong"].copy()
    plays["start_time"] = pd.to_datetime(plays["ts"], unit="ms")
    plays["play_day"] = plays["start_time"].dt.date
    plays["track"] = plays["song"] + " — " + plays["artist"]
    plays["weekday"] = plays["start_time"].dt.day_name()
    return plays


def get_top_tracks(df: pd.DataFrame, top_n: int = 10) -> pd.DataFrame:
    track_col = "track" if "track" in df.columns else "song"
    return (
        df.groupby(track_col, as_index=False)
        .size()
        .rename(columns={"size": "play_count"})
        .sort_values("play_count", ascending=False)
        .head(top_n)
    )


def get_daily_plays(df: pd.DataFrame) -> pd.DataFrame:
    return (
        df.groupby("play_day", as_index=False)
        .size()
        .rename(columns={"size": "play_count"})
        .sort_values("play_day")
    )


def get_plays_by_user(df: pd.DataFrame) -> pd.DataFrame:
    if "first_name" in df.columns:
        user_col = df["first_name"] + " " + df["last_name"]
    else:
        user_col = df["firstName"] + " " + df["lastName"]

    result = df.copy()
    result["user"] = user_col
    return (
        result.groupby("user", as_index=False)
        .size()
        .rename(columns={"size": "play_count"})
        .sort_values("play_count", ascending=False)
    )


def get_plays_by_level(df: pd.DataFrame) -> pd.DataFrame:
    return (
        df.groupby("level", as_index=False)
        .size()
        .rename(columns={"size": "play_count"})
        .sort_values("play_count", ascending=False)
    )


def get_plays_by_weekday(df: pd.DataFrame) -> pd.DataFrame:
    weekday_col = "weekday" if "weekday" in df.columns else df["start_time"].dt.day_name()
    result = df.copy()
    result["weekday"] = weekday_col
    order = [
        "Monday",
        "Tuesday",
        "Wednesday",
        "Thursday",
        "Friday",
        "Saturday",
        "Sunday",
    ]
    grouped = (
        result.groupby("weekday", as_index=False)
        .size()
        .rename(columns={"size": "play_count"})
    )
    grouped["weekday"] = pd.Categorical(grouped["weekday"], categories=order, ordered=True)
    return grouped.sort_values("weekday")


def plot_top_tracks(df: pd.DataFrame, top_n: int = 10, save_path: Path | None = None) -> plt.Figure:
    """Barplot: самые часто прослушиваемые треки."""
    data = get_top_tracks(df, top_n=top_n)
    fig, ax = plt.subplots()
    sns.barplot(data=data, y="track", x="play_count", ax=ax, hue="track", legend=False)
    ax.set_title("Топ прослушиваемых треков")
    ax.set_xlabel("Количество прослушиваний")
    ax.set_ylabel("Трек")
    fig.tight_layout()
    if save_path:
        fig.savefig(save_path, dpi=150, bbox_inches="tight")
    return fig


def plot_daily_plays(df: pd.DataFrame, save_path: Path | None = None) -> plt.Figure:
    """Lineplot: активность прослушиваний по дням."""
    data = get_daily_plays(df)
    data["play_day"] = pd.to_datetime(data["play_day"])
    fig, ax = plt.subplots()
    sns.lineplot(data=data, x="play_day", y="play_count", marker="o", ax=ax)
    ax.set_title("Прослушивания по дням")
    ax.set_xlabel("Дата")
    ax.set_ylabel("Количество прослушиваний")
    fig.tight_layout()
    if save_path:
        fig.savefig(save_path, dpi=150, bbox_inches="tight")
    return fig


def plot_user_activity(df: pd.DataFrame, save_path: Path | None = None) -> plt.Figure:
    """Barplot: активность пользователей."""
    data = get_plays_by_user(df)
    fig, ax = plt.subplots()
    sns.barplot(data=data, x="user", y="play_count", ax=ax, hue="user", legend=False)
    ax.set_title("Активность пользователей")
    ax.set_xlabel("Пользователь")
    ax.set_ylabel("Количество прослушиваний")
    plt.xticks(rotation=20, ha="right")
    fig.tight_layout()
    if save_path:
        fig.savefig(save_path, dpi=150, bbox_inches="tight")
    return fig


def plot_plays_by_level(df: pd.DataFrame, save_path: Path | None = None) -> plt.Figure:
    """Countplot: распределение прослушиваний по уровню подписки."""
    fig, ax = plt.subplots()
    sns.countplot(data=df, x="level", ax=ax, order=sorted(df["level"].dropna().unique()))
    ax.set_title("Прослушивания по уровню подписки")
    ax.set_xlabel("Уровень")
    ax.set_ylabel("Количество прослушиваний")
    fig.tight_layout()
    if save_path:
        fig.savefig(save_path, dpi=150, bbox_inches="tight")
    return fig


def plot_plays_by_weekday(df: pd.DataFrame, save_path: Path | None = None) -> plt.Figure:
    """Barplot: прослушивания по дням недели."""
    data = get_plays_by_weekday(df)
    fig, ax = plt.subplots()
    sns.barplot(data=data, x="weekday", y="play_count", ax=ax, hue="weekday", legend=False)
    ax.set_title("Прослушивания по дням недели")
    ax.set_xlabel("День недели")
    ax.set_ylabel("Количество прослушиваний")
    fig.tight_layout()
    if save_path:
        fig.savefig(save_path, dpi=150, bbox_inches="tight")
    return fig


def plot_artist_popularity(df: pd.DataFrame, save_path: Path | None = None) -> plt.Figure:
    """Barplot: популярность исполнителей."""
    artist_col = "name" if "name" in df.columns else "artist"
    data = (
        df.groupby(artist_col, as_index=False)
        .size()
        .rename(columns={"size": "play_count", artist_col: "artist"})
        .sort_values("play_count", ascending=False)
    )
    fig, ax = plt.subplots()
    sns.barplot(data=data, x="artist", y="play_count", ax=ax, hue="artist", legend=False)
    ax.set_title("Популярность исполнителей")
    ax.set_xlabel("Исполнитель")
    ax.set_ylabel("Количество прослушиваний")
    plt.xticks(rotation=20, ha="right")
    fig.tight_layout()
    if save_path:
        fig.savefig(save_path, dpi=150, bbox_inches="tight")
    return fig


def save_all_plots(
    df: pd.DataFrame,
    output_dir: Path = PLOTS_PATH,
    show: bool = False,
) -> dict[str, Path]:
    """Строит и сохраняет все графики."""
    output_dir.mkdir(parents=True, exist_ok=True)
    plots = {
        "top_tracks": plot_top_tracks(df, save_path=output_dir / "top_tracks.png"),
        "daily_plays": plot_daily_plays(df, save_path=output_dir / "daily_plays.png"),
        "user_activity": plot_user_activity(df, save_path=output_dir / "user_activity.png"),
        "plays_by_level": plot_plays_by_level(df, save_path=output_dir / "plays_by_level.png"),
        "plays_by_weekday": plot_plays_by_weekday(df, save_path=output_dir / "plays_by_weekday.png"),
        "artist_popularity": plot_artist_popularity(
            df, save_path=output_dir / "artist_popularity.png"
        ),
    }
    if show:
        plt.show()
    else:
        plt.close("all")
    return {name: output_dir / f"{name}.png" for name in plots}


def load_data(source: str = "auto", output_path: Path = OUTPUT_PATH) -> pd.DataFrame:
    if source == "parquet" or (source == "auto" and (output_path / "songplays").exists()):
        return load_songplays_from_parquet(output_path)
    return load_songplays_from_json()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Seaborn visualization for Sparkify data")
    parser.add_argument(
        "--source",
        choices=("auto", "parquet", "json"),
        default="auto",
        help="Источник данных: parquet после ETL или json-логи",
    )
    parser.add_argument("--output", type=Path, default=OUTPUT_PATH)
    parser.add_argument("--plots-dir", type=Path, default=PLOTS_PATH)
    parser.add_argument("--show", action="store_true", help="Показать графики на экране")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    setup_style()
    df = load_data(args.source, args.output)
    paths = save_all_plots(df, output_dir=args.plots_dir, show=args.show)
    print("Графики сохранены:")
    for name, path in paths.items():
        print(f"  {name}: {path}")


if __name__ == "__main__":
    main()
