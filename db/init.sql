-- init.sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100),
    email VARCHAR(150) UNIQUE
);

CREATE TABLE playlists (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    title VARCHAR(200)
);

CREATE TABLE songs (
    id SERIAL PRIMARY KEY,
    playlist_id INTEGER REFERENCES playlists(id),
    title VARCHAR(200),
    artist VARCHAR(150)
);

-- TODO: Inserir mais inserts e rebuildar o container do postgres
INSERT INTO users (name, email) VALUES
('Alice', 'alice@example.com'),
('Bob', 'bob@example.com');

INSERT INTO playlists (user_id, title) VALUES
(1, 'Alice Favorites'),
(2, 'Bob Chill Playlist');

INSERT INTO songs (playlist_id, title, artist) VALUES
(1, 'Song A', 'Artist 1'),
(1, 'Song B', 'Artist 2'),
(2, 'Song C', 'Artist 3'),
(2, 'Song D', 'Artist 4');

