import strawberry
from fastapi import FastAPI, Request, Response
from strawberry.fastapi import GraphQLRouter
from starlette.requests import ClientDisconnect
from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, Table
from sqlalchemy.orm import sessionmaker, declarative_base, relationship, joinedload
import os
from typing import List

DB_URL = f"postgresql+psycopg2://{os.getenv('DB_USER')}:{os.getenv('DB_PASS')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
engine = create_engine(DB_URL)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

playlist_songs_table = Table(
    'playlist_songs', Base.metadata,
    Column('playlist_id', Integer, ForeignKey('playlists.id')),
    Column('song_id', Integer, ForeignKey('songs.id'))
)

class UserModel(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    name = Column(String)
    age = Column(Integer)
    playlists = relationship("PlaylistModel", back_populates="user")

class PlaylistModel(Base):
    __tablename__ = "playlists"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    name = Column(String)
    user = relationship("UserModel", back_populates="playlists")
    songs = relationship("SongModel", secondary=playlist_songs_table, back_populates="playlists")

class SongModel(Base):
    __tablename__ = "songs"
    id = Column(Integer, primary_key=True)
    title = Column(String)
    artist = Column(String)
    playlists = relationship("PlaylistModel", secondary=playlist_songs_table, back_populates="songs")

@strawberry.type
class Song:
    id: int
    title: str
    artist: str

@strawberry.type
class Playlist:
    id: int
    name: str
    songs: List[Song]

@strawberry.type
class User:
    id: int
    name: str
    age: int
    playlists: List[Playlist]

@strawberry.type
class Query:
    @strawberry.field
    def users(self) -> List[User]:
        db = SessionLocal()
        users = db.query(UserModel).options(joinedload(UserModel.playlists).joinedload(PlaylistModel.songs)).all()
        db.close()

        res = []
        for u in users:
            pl_list = [
                Playlist(id=p.id, name=p.name, songs=[
                    Song(id=s.id, title=s.title, artist=s.artist) for s in p.songs
                ]) for p in u.playlists
            ]
            res.append(User(id=u.id, name=u.name, age=u.age, playlists=pl_list))
        return res

    @strawberry.field
    def songs(self) -> List[Song]:
        db = SessionLocal()
        songs = db.query(SongModel).all()
        db.close()
        return [Song(id=s.id, title=s.title, artist=s.artist) for s in songs]

    @strawberry.field
    def user_playlists(self, user_id: int) -> List[Playlist]:
        db = SessionLocal()
        playlists = db.query(PlaylistModel).filter(PlaylistModel.user_id == user_id).options(joinedload(PlaylistModel.songs)).all()
        db.close()
        return [Playlist(id=p.id, name=p.name, songs=[
            Song(id=s.id, title=s.title, artist=s.artist) for s in p.songs
        ]) for p in playlists]

    @strawberry.field
    def playlist_songs(self, playlist_id: int) -> List[Song]:
        db = SessionLocal()
        playlist = db.query(PlaylistModel).filter(PlaylistModel.id == playlist_id).options(joinedload(PlaylistModel.songs)).first()
        db.close()
        if not playlist: return []
        return [Song(id=s.id, title=s.title, artist=s.artist) for s in playlist.songs]

    @strawberry.field
    def playlists_by_song(self, song_id: int) -> List[Playlist]:
        db = SessionLocal()
        playlists = db.query(PlaylistModel).join(PlaylistModel.songs).filter(SongModel.id == song_id).options(joinedload(PlaylistModel.songs)).all()
        db.close()
        return [Playlist(id=p.id, name=p.name, songs=[
             Song(id=s.id, title=s.title, artist=s.artist) for s in p.songs
        ]) for p in playlists]

schema = strawberry.Schema(query=Query)
graphql_app = GraphQLRouter(schema)
app = FastAPI()

@app.exception_handler(ClientDisconnect)
async def client_disconnect_handler(request: Request, exc: ClientDisconnect):
    print("Client disconnected unexpectedly (Locust stopped)")
    return Response(status_code=499)

app.include_router(graphql_app, prefix="/graphql")
