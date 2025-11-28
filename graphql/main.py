import strawberry
from fastapi import FastAPI
from strawberry.fastapi import GraphQLRouter
from sqlalchemy import create_engine, Column, Integer, String, ForeignKey
from sqlalchemy.orm import sessionmaker, declarative_base, relationship, joinedload
import os
from typing import List

DB_URL = f"postgresql+psycopg2://{os.getenv('DB_USER')}:{os.getenv('DB_PASS')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
engine = create_engine(DB_URL)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

# --- SQLAlchemy Models ---
class UserModel(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    name = Column(String)
    email = Column(String)
    playlists = relationship("PlaylistModel", back_populates="user")

class PlaylistModel(Base):
    __tablename__ = "playlists"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    title = Column(String)
    user = relationship("UserModel", back_populates="playlists")
    songs = relationship("SongModel", back_populates="playlist")

class SongModel(Base):
    __tablename__ = "songs"
    id = Column(Integer, primary_key=True)
    playlist_id = Column(Integer, ForeignKey("playlists.id"))
    title = Column(String)
    artist = Column(String)
    playlist = relationship("PlaylistModel", back_populates="songs")

# --- GraphQL Types ---
@strawberry.type
class Song:
    id: int
    title: str
    artist: str

@strawberry.type
class Playlist:
    id: int
    title: str
    songs: List[Song]

@strawberry.type
class User:
    id: int
    name: str
    email: str
    playlists: List[Playlist]

@strawberry.type
class Query:
    @strawberry.field
    def users(self) -> List[User]:
        db = SessionLocal()
        # Use joinedload to prevent N+1 queries
        users_db = db.query(UserModel).options(
            joinedload(UserModel.playlists).joinedload(PlaylistModel.songs)
        ).all()
        
        # Manual Mapping (or use a library like strawberry-sqlalchemy-mapper in prod)
        result = []
        for u in users_db:
            p_list = []
            for p in u.playlists:
                s_list = [Song(id=s.id, title=s.title, artist=s.artist) for s in p.songs]
                p_list.append(Playlist(id=p.id, title=p.title, songs=s_list))
            result.append(User(id=u.id, name=u.name, email=u.email, playlists=p_list))
        
        db.close()
        return result

schema = strawberry.Schema(query=Query)
graphql_app = GraphQLRouter(schema)
app = FastAPI()
app.include_router(graphql_app, prefix="/graphql")
