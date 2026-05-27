-- Дополнительная аналитика по прослушиваниям

-- 1. Самый популярный трек по дням
SELECT
    DATE(sp.start_time) AS play_day,
    s.title,
    a.name AS artist_name,
    COUNT(*) AS play_count
FROM songplays sp
JOIN songs s ON sp.song_id = s.song_id
JOIN artists a ON sp.artist_id = a.artist_id
GROUP BY play_day, s.title, a.name
QUALIFY ROW_NUMBER() OVER (PARTITION BY play_day ORDER BY COUNT(*) DESC) = 1
ORDER BY play_day;

-- 2. Самые часто прослушиваемые треки (за всё время)
SELECT
    s.title,
    a.name AS artist_name,
    COUNT(*) AS total_plays
FROM songplays sp
JOIN songs s ON sp.song_id = s.song_id
JOIN artists a ON sp.artist_id = a.artist_id
GROUP BY s.title, a.name
ORDER BY total_plays DESC;

-- 3. Самые популярные треки за неделю
SELECT
    t.week,
    t.year,
    s.title,
    a.name AS artist_name,
    COUNT(*) AS weekly_plays
FROM songplays sp
JOIN time_table t ON sp.start_time = t.start_time
JOIN songs s ON sp.song_id = s.song_id
JOIN artists a ON sp.artist_id = a.artist_id
GROUP BY t.week, t.year, s.title, a.name
QUALIFY ROW_NUMBER() OVER (PARTITION BY t.week, t.year ORDER BY COUNT(*) DESC) = 1
ORDER BY t.year, t.week;

-- 4. Самые популярные треки за месяц
SELECT
    t.month,
    t.year,
    s.title,
    a.name AS artist_name,
    COUNT(*) AS monthly_plays
FROM songplays sp
JOIN time_table t ON sp.start_time = t.start_time
JOIN songs s ON sp.song_id = s.song_id
JOIN artists a ON sp.artist_id = a.artist_id
GROUP BY t.month, t.year, s.title, a.name
QUALIFY ROW_NUMBER() OVER (PARTITION BY t.month, t.year ORDER BY COUNT(*) DESC) = 1
ORDER BY t.year, t.month;
