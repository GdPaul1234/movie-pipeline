CREATE TABLE IF NOT EXISTS people (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    UNIQUE(name)
);

CREATE TABLE IF NOT EXISTS genres (
    id INTEGER PRIMARY KEY,
    genre TEXT NOT NULL,
    UNIQUE(genre)
);

CREATE TABLE IF NOT EXISTS people_mediable_relation (
    id INTEGER PRIMARY KEY,
    person_id INTEGER NOT NULL,
    media_type VARCHAR(8) NOT NULL CHECK(media_type in ('movie', 'serie', 'episode')),
    media_id INTEGER NOT NULL,
    relation VARCHAR(10) NOT NULL CHECK(relation in ('credit', 'director', 'actor')),
    FOREIGN KEY(person_id) REFERENCES people(id),
    UNIQUE(person_id, media_type, media_id, relation)
);

CREATE TABLE IF NOT EXISTS mediable_genres (
    id INTEGER PRIMARY KEY,
    media_type VARCHAR(8) NOT NULL CHECK(media_type in ('movie', 'episode')),
    media_id INTEGER NOT NULL,
    genre_id INTEGER NOT NULL,
    FOREIGN KEY(genre_id) REFERENCES genres(id),
    UNIQUE(media_type, media_id, genre_id)
);

CREATE TABLE IF NOT EXISTS movies (
    id INTEGER PRIMARY KEY,
    title TEXT NOT NULL,
    year INTEGER NOT NULL,
    rating DECIMAL(2,6) NOT NULL,
    mpaa VARCHAR(10),
    UNIQUE(title, year)
);

CREATE TABLE IF NOT EXISTS series (
    id INTEGER PRIMARY KEY,
    title TEXT NOT NULL,
    year INTEGER NOT NULL,
    rating DECIMAL(2,6) NOT NULL,
    mpaa VARCHAR(10),
    UNIQUE(title, year)
);

CREATE TABLE IF NOT EXISTS episodes (
    id INTEGER PRIMARY KEY,
    serie_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    season INTEGER NOT NULL,
    episode INTEGER NOT NULL,
    year INTEGER NOT NULL,
    rating DECIMAL(2,6) NOT NULL,
    mpaa VARCHAR(10),
    FOREIGN KEY(serie_id) REFERENCES series(id),
    UNIQUE(serie_id, season, episode)
);

CREATE TABLE IF NOT EXISTS medias (
    id INTEGER PRIMARY KEY,
    filepath TEXT NOT NULL,
    duration  DECIMAL(10,6) NOT NULL,
    created_at INTEGER NOT NULL,
    media_type VARCHAR(8) NOT NULL CHECK(media_type in ('movie', 'episode')),
    media_id INTEGER NOT NULL,
    UNIQUE(media_type, media_id),
    UNIQUE(filepath)
);
