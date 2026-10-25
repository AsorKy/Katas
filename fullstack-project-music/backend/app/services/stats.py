import pandas as pd


def top_genres(rows: pd.DataFrame, limit: int) -> list[dict]:
    per_song = rows.drop_duplicates(subset=["song_id", "genre_id"])
    stats = per_song.groupby(
        ["genre_id", "name"], as_index=False
    ).agg(
        song_count=("song_id", "count"),
        avg_duration_s=("duration_s", "mean")
    )

    playlists = rows.groupby("genre_id", as_index=False).agg(
        playlist_count=("playlist_id", "nunique")
    )

    stats = stats.merge(playlists, on="genre_id", how="left")
    stats["avg_duration_s"] = stats["avg_duration_s"].fillna(0).round(1)
    stats = stats.sort_values(
        ["playlist_count", "song_count", "name"], 
        ascending=[False, False, True]
    ).head(limit)

    return stats.astype({
        "song_count": int,
        "playlist_count": int,
        "avg_duration_s": float
    }).to_dict(orient="records")
