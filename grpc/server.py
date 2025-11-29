import grpc
from concurrent import futures
import demo_pb2
import demo_pb2_grpc
import os
from sqlalchemy import create_engine, text
from grpc_health.v1 import health, health_pb2, health_pb2_grpc

class UserService(demo_pb2_grpc.UserServiceServicer):
    def __init__(self):
        try:
            DB_URL = f"postgresql+psycopg2://{os.getenv('DB_USER')}:{os.getenv('DB_PASS')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
            self.engine = create_engine(DB_URL)
        except Exception as e:
            print(f"Failed to connect to DB: {e}")

    def GetAllUsers(self, request, context):
        with self.engine.connect() as conn:
            users = conn.execute(text("SELECT id, name, age FROM users")).fetchall()
            response = []
            for u in users:
                response.append(demo_pb2.UserResponse(id=u[0], name=u[1], age=u[2]))
            return demo_pb2.UserList(users=response)

    def GetAllSongs(self, request, context):
        with self.engine.connect() as conn:
            songs = conn.execute(text("SELECT id, title, artist FROM songs")).fetchall()
            return demo_pb2.SongList(songs=[
                demo_pb2.Song(id=s[0], title=s[1], artist=s[2]) for s in songs
            ])

    def GetUserPlaylists(self, request, context):
        with self.engine.connect() as conn:
            playlists = conn.execute(text("SELECT id, name FROM playlists WHERE user_id = :uid"), {"uid": request.id}).fetchall()
            pl_protos = []
            for p in playlists:
                songs = conn.execute(text("""
                    SELECT s.id, s.title, s.artist 
                    FROM songs s 
                    JOIN playlist_songs ps ON s.id = ps.song_id 
                    WHERE ps.playlist_id = :pid
                """), {"pid": p[0]}).fetchall()
                
                s_protos = [demo_pb2.Song(id=s[0], title=s[1], artist=s[2]) for s in songs]
                pl_protos.append(demo_pb2.Playlist(id=p[0], name=p[1], songs=s_protos))
            return demo_pb2.PlaylistList(playlists=pl_protos)

    def GetPlaylistSongs(self, request, context):
        with self.engine.connect() as conn:
            songs = conn.execute(text("""
                SELECT s.id, s.title, s.artist 
                FROM songs s 
                JOIN playlist_songs ps ON s.id = ps.song_id 
                WHERE ps.playlist_id = :pid
            """), {"pid": request.id}).fetchall()
            return demo_pb2.SongList(songs=[
                demo_pb2.Song(id=s[0], title=s[1], artist=s[2]) for s in songs
            ])

    def GetPlaylistsBySong(self, request, context):
        with self.engine.connect() as conn:
            playlists = conn.execute(text("""
                SELECT p.id, p.name 
                FROM playlists p 
                JOIN playlist_songs ps ON p.id = ps.playlist_id 
                WHERE ps.song_id = :sid
            """), {"sid": request.id}).fetchall()
            
            pl_protos = []
            for p in playlists:
                songs = conn.execute(text("""
                    SELECT s.id, s.title, s.artist 
                    FROM songs s 
                    JOIN playlist_songs ps ON s.id = ps.song_id 
                    WHERE ps.playlist_id = :pid
                """), {"pid": p[0]}).fetchall()
                s_protos = [demo_pb2.Song(id=s[0], title=s[1], artist=s[2]) for s in songs]
                pl_protos.append(demo_pb2.Playlist(id=p[0], name=p[1], songs=s_protos))
            return demo_pb2.PlaylistList(playlists=pl_protos)

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    
    health_servicer = health.HealthServicer()
    health_servicer.set("", health_pb2.HealthCheckResponse.SERVING)
    health_pb2_grpc.add_HealthServicer_to_server(health_servicer, server)
    
    demo_pb2_grpc.add_UserServiceServicer_to_server(UserService(), server)
    
    server.add_insecure_port("[::]:50051")
    print("Server started on port 50051")
    
    server.start()
    server.wait_for_termination()

if __name__ == '__main__': serve()
