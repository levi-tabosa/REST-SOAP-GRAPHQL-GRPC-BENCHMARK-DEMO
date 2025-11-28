
import grpc
from concurrent import futures
import demo_pb2
import demo_pb2_grpc
import os
from sqlalchemy import create_engine, text

class UserService(demo_pb2_grpc.UserServiceServicer):
    def __init__(self):
        DB_URL = f"postgresql+psycopg2://{os.getenv('DB_USER')}:{os.getenv('DB_PASS')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
        self.engine = create_engine(DB_URL)

    def GetUser(self, request, context):
        with self.engine.connect() as conn:
            # 1. Get User
            user_row = conn.execute(
                text("SELECT id, name, email FROM users WHERE id = :id"), 
                {"id": request.id}
            ).fetchone()
            
            if not user_row:
                context.set_code(grpc.StatusCode.NOT_FOUND)
                return demo_pb2.UserResponse()

            # 2. Get Playlists
            playlists_rows = conn.execute(
                text("SELECT id, title FROM playlists WHERE user_id = :uid"),
                {"uid": request.id}
            ).fetchall()

            pb_playlists = []
            for p_row in playlists_rows:
                # 3. Get Songs for Playlist
                songs_rows = conn.execute(
                    text("SELECT title, artist FROM songs WHERE playlist_id = :pid"),
                    {"pid": p_row[0]}
                ).fetchall()
                
                pb_songs = [demo_pb2.Song(title=s[0], artist=s[1]) for s in songs_rows]
                pb_playlists.append(demo_pb2.Playlist(id=p_row[0], title=p_row[1], songs=pb_songs))

            return demo_pb2.UserResponse(
                id=user_row[0], 
                name=user_row[1], 
                email=user_row[2], 
                playlists=pb_playlists
            )


def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    demo_pb2_grpc.add_UserServiceServicer_to_server(UserService(), server)
    server.add_insecure_port('[::]:50051')
    print("Server started on port 50051")
    server.start()
    server.wait_for_termination()

if __name__ == '__main__':
    serve()
