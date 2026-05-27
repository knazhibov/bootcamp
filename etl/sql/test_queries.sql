-- Проверка качества данных после ETL

SELECT 'artists' AS table_name, COUNT(*) AS row_count FROM artists
UNION ALL
SELECT 'songs', COUNT(*) FROM songs
UNION ALL
SELECT 'users', COUNT(*) FROM users
UNION ALL
SELECT 'time_table', COUNT(*) FROM time_table
UNION ALL
SELECT 'songplays', COUNT(*) FROM songplays;

-- Проверка связей в fact-таблице
SELECT COUNT(*) AS orphan_songplays
FROM songplays sp
LEFT JOIN songs s ON sp.song_id = s.song_id
WHERE s.song_id IS NULL;

-- Пример выборки для рекомендательных моделей
SELECT
    u.user_id,
    u.first_name,
    u.last_name,
    s.title AS song,
    a.name AS artist,
    sp.start_time
FROM songplays sp
JOIN users u ON sp.user_id = u.user_id
JOIN songs s ON sp.song_id = s.song_id
JOIN artists a ON sp.artist_id = a.artist_id
ORDER BY u.user_id, sp.start_time;
