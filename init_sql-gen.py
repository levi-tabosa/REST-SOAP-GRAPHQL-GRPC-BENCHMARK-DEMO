import random
from faker import Faker

fake = Faker()

NUM_USERS = 1000
NUM_SONGS = 5000
NUM_PLAYLISTS = 1500
AVG_SONGS_PER_PLAYLIST = 20

output = []

# DROP + CREATE
output.append("""
DROP TABLE IF EXISTS playlist_songs;
DROP TABLE IF EXISTS songs;
DROP TABLE IF EXISTS playlists;
DROP TABLE IF EXISTS users;

CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    age INT
);

CREATE TABLE songs (
    id SERIAL PRIMARY KEY,
    title VARCHAR(200) NOT NULL,
    artist VARCHAR(150) NOT NULL
);

CREATE TABLE playlists (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(200) NOT NULL
);

CREATE TABLE playlist_songs (
    playlist_id INTEGER NOT NULL REFERENCES playlists(id) ON DELETE CASCADE,
    song_id INTEGER NOT NULL REFERENCES songs(id) ON DELETE CASCADE,
    PRIMARY KEY (playlist_id, song_id)
);
""")

print("Generating users...")
user_rows = []
for i in range(NUM_USERS):
    name = fake.name().replace("'", "")
    age = random.randint(18, 70)
    user_rows.append(f"('{name}', {age})")

output.append("INSERT INTO users (name, age) VALUES\n" +
              ",\n".join(user_rows) + ";\n")


print("Generating songs...")
song_rows = []
for i in range(NUM_SONGS):
    title = fake.sentence(nb_words=3).replace("'", "")
    artist = fake.name().replace("'", "")
    song_rows.append(f"('{title}', '{artist}')")

output.append("INSERT INTO songs (title, artist) VALUES\n" +
              ",\n".join(song_rows) + ";\n")


print("Generating playlists...")
playlist_rows = []
for i in range(NUM_PLAYLISTS):
    user_id = random.randint(1, NUM_USERS)
    name = fake.catch_phrase().replace("'", "")
    playlist_rows.append(f"({user_id}, '{name}')")

output.append("INSERT INTO playlists (user_id, name) VALUES\n" +
              ",\n".join(playlist_rows) + ";\n")


print("Generating playlist-song relationships...")
ps_rows = []
for pid in range(1, NUM_PLAYLISTS + 1):
    num_songs = random.randint(10, 40)
    songs = random.sample(range(1, NUM_SONGS + 1), num_songs)
    for sid in songs:
        ps_rows.append(f"({pid}, {sid})")

output.append("INSERT INTO playlist_songs (playlist_id, song_id) VALUES\n" +
              ",\n".join(ps_rows) + ";\n")

print("Saving to dataset.sql...")
with open("dataset.sql", "w") as f:
    f.write("\n".join(output))

print("DONE! dataset.sql generated successfully.")
