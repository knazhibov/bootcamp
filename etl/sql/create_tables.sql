-- Звёздная схема для музыкального сервиса Сбер
-- Dimension-таблицы и fact-таблица songplays

CREATE TABLE IF NOT EXISTS artists (
    artist_id VARCHAR(64) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    location VARCHAR(255),
    latitude DOUBLE PRECISION,
    longitude DOUBLE PRECISION
);

CREATE TABLE IF NOT EXISTS songs (
    song_id VARCHAR(64) PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    artist_id VARCHAR(64) NOT NULL REFERENCES artists(artist_id),
    year INTEGER,
    duration DOUBLE PRECISION
);

CREATE TABLE IF NOT EXISTS users (
    user_id VARCHAR(64) PRIMARY KEY,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    gender CHAR(1),
    level VARCHAR(20)
);

CREATE TABLE IF NOT EXISTS time_table (
    start_time TIMESTAMP PRIMARY KEY,
    hour INTEGER NOT NULL,
    day INTEGER NOT NULL,
    week INTEGER NOT NULL,
    month INTEGER NOT NULL,
    year INTEGER NOT NULL,
    weekday INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS songplays (
    songplay_id BIGSERIAL PRIMARY KEY,
    start_time TIMESTAMP NOT NULL REFERENCES time_table(start_time),
    user_id VARCHAR(64) NOT NULL REFERENCES users(user_id),
    level VARCHAR(20),
    session_id INTEGER NOT NULL,
    location VARCHAR(255),
    user_agent TEXT,
    song_id VARCHAR(64) NOT NULL REFERENCES songs(song_id),
    artist_id VARCHAR(64) NOT NULL REFERENCES artists(artist_id)
);

CREATE INDEX IF NOT EXISTS idx_songplays_start_time ON songplays(start_time);
CREATE INDEX IF NOT EXISTS idx_songplays_user_id ON songplays(user_id);
CREATE INDEX IF NOT EXISTS idx_songplays_song_id ON songplays(song_id);
CREATE INDEX IF NOT EXISTS idx_songplays_artist_id ON songplays(artist_id);
