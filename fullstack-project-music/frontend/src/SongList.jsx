import { useEffect, useState } from "react";

const API = "http://localhost:8000";

function formatDuration(totalSeconds) {
    const minutes = Math.floor(totalSeconds / 60);
    const seconds = String(totalSeconds % 60).padStart(2, "0");
    return `${minutes}:${seconds}`;
}

export default function SongList() {
    const [q, setQ] = useState("");
    const [songs, setSongs] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        const controller = new AbortController();

        async function load() {
            try {
                const params = new URLSearchParams();
                if (q) params.set("q", q);
                const res = await fetch(`${API}/songs?${params}`, { signal: controller.signal });
                if (!res.ok) throw new Error(`HTTP ${res.status}`);
                setSongs(await res.json());
                setError(null);
                setLoading(false);
            } catch (err) {
                if (err.name === "AbortError") return;
                setError(err.message);
                setLoading(false);
            }
        }

        load();
        return () => controller.abort();
    }, [q]);

    let content;
    if (loading) content = <p>Cargando…</p>;
    else if (error) content = <p role="alert">Error: {error}</p>;
    else if (songs.length === 0) content = <p>No hay canciones.</p>;
    else
        content = (
            <ul>
                {songs.map((song) => (
                    <li key={song.id}>
                        <strong>{song.title}</strong> — {song.artists.map((a) => a.name).join(", ")} ·{" "}
                        {song.genre.name} · {formatDuration(song.duration_s)}
                    </li>
                ))}
            </ul>
        );

    return (
        <>
            <input
                type="search"
                value={q}
                onChange={(e) => setQ(e.target.value)}
                placeholder="Buscar cancion..."
                aria-label="Buscar cancion"
            />
            {content}
        </>
    );
}