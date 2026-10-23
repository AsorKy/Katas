-- Consultas de la lección 5. Probarlas a mano sobre la base sembrada:
--   uv run python -m app.seed
--   sqlite3 -header -column data/music.db < sql/queries.sql
-- Los valores (ids, 'a', 20...) son de ejemplo: en el código serán parámetros.
-- En Q2 cada condición es opcional: bórrala para ver el efecto del filtro.

-- Q1. Géneros (GET /genres)
SELECT id, name, created_at
FROM genres
ORDER BY id;

-- Q2. Canciones con filtros opcionales y paginación (GET /songs)
--     Filtro por artista con IN (subconsulta), no con JOIN: así cada canción
--     sale una sola vez y no se pierden sus otros artistas.
SELECT s.id, s.title, s.duration_s, s.genre_id
FROM songs s
WHERE s.genre_id = 1                                              -- ?genre_id=
  AND s.id IN (SELECT song_id FROM song_artists WHERE artist_id = 1)   -- ?artist_id=
  AND LOWER(s.title) LIKE '%' || LOWER('a') || '%'                -- ?q=
ORDER BY s.id
LIMIT 20 OFFSET 0;                                                -- ?limit= &offset=

-- Q3. Artistas (con rol) de un grupo de canciones: UNA consulta para todas
--     las canciones de la página, en vez de una por canción (evita el N+1).
SELECT sa.song_id, a.id AS artist_id, a.name, sa.role
FROM song_artists sa
JOIN artists a ON a.id = sa.artist_id
WHERE sa.song_id IN (1, 2, 3)
ORDER BY sa.song_id, a.id;

-- Q4. Géneros distintos de un artista (ArtistsOut.genres, dato calculado)
SELECT DISTINCT g.name
FROM genres g
JOIN songs s         ON s.genre_id = g.id
JOIN song_artists sa ON sa.song_id = s.id
WHERE sa.artist_id = 1
ORDER BY g.name;

-- Q5. Estadísticas de un artista (GET /artists/{id}/stats)
--     song_count: la PK (song_id, artist_id) ya garantiza canciones distintas.
--     playlist_count: COUNT(DISTINCT ...) porque una playlist con 5 canciones
--     del artista cuenta una sola vez.
SELECT
  (SELECT COUNT(*) FROM song_artists WHERE artist_id = 1) AS song_count,
  (SELECT COUNT(DISTINCT ps.playlist_id)
     FROM playlist_songs ps
     JOIN song_artists sa ON sa.song_id = ps.song_id
    WHERE sa.artist_id = 1)                                AS playlist_count;
