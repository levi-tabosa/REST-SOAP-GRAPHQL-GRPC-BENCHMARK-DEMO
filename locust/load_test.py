# load_test.py
import time
import requests
import random
from locust import HttpUser, User, task, between, events

try:
    from grpc_tools import protoc
    protoc.main((
        '',
        '-I.',
        '--python_out=.',
        '--grpc_python_out=.',
        'demo.proto',
    ))
    import grpc
    import demo_pb2
    import demo_pb2_grpc
    from grpc_health.v1 import health_pb2, health_pb2_grpc
except ImportError as e:
    print(f"[ERROR] Could not import grpc/protoc. Dependencies missing? {e}")
    sys.exit(1)
except Exception as e:
    print(f"[ERROR] Failed to compile proto file. Is demo.proto in the locust folder? {e}")
    sys.exit(1)

HOSTS = {
    "rest": "http://rest-api:8080",
    "soap": "http://soap-api:8080", 
    "graphql": "http://graphql-api:8000",
    "grpc": "grpc-api:50051"
}

def is_grpc_active(timeout=2):
    try:
        target = HOSTS["grpc"]
        channel = grpc.insecure_channel(target)
        health_stub = health_pb2_grpc.HealthStub(channel)

        request = health_pb2.HealthCheckRequest(service="")
        response = health_stub.Check(request, timeout=timeout)

        channel.close()
        return response.status == health_pb2.HealthCheckResponse.SERVING
    except Exception as e:
        return False

def is_service_active(service: str) -> bool:
    if service == "grpc":
        return is_grpc_active()
    
    url = HOSTS[service]
    try:
        if service == "rest":
            response = requests.get(f"{url}/actuator/health", timeout=2)
        elif service == "graphql":
            response = requests.get(f"{url}/graphql", timeout=2)
        elif service == "soap":
            response = requests.get(f"{url}/actuator/healthws", timeout=2)
        else:
            response = requests.get(url, timeout=2)
        
        return response.status_code < 500
    except requests.exceptions.RequestException:
        return False

def detect_active_services(max_attempts=10, delay=5):
    print("[Locust Init] Starting service discovery...")
    
    for attempt in range(1, max_attempts + 1):
        active = {}
        for service in HOSTS.keys():
            is_active = is_service_active(service)
            active[service] = is_active
            if is_active:
                print(f" >> {service} is active at {HOSTS[service]}")
            
        if any(active.values()):
            print("[Locust Init] Active services found!")
            return active

        if attempt < max_attempts:
            print(f"[Locust Init] No services yet. Waiting {delay}s...")
            time.sleep(delay)

    print("[Locust Init] No services found after all attempts.")
    return {k: False for k in HOSTS}

ACTIVE_SERVICES = detect_active_services()
print("Final active services:", ACTIVE_SERVICES)

if ACTIVE_SERVICES.get("rest"):
    class RestApiUser(HttpUser):
        host = HOSTS["rest"]
        wait_time = between(1, 2)

        @task(1)
        def list_all_users(self):
            self.client.get("/users", name="/users")

        @task(1)
        def list_all_songs(self):
            self.client.get("/songs", name="/songs")

        @task(2)
        def list_user_playlists(self):
            self.client.get("/users/1/playlists", name="/users/1/playlists")

        @task(2)
        def list_playlist_songs(self):
            self.client.get("/playlists/1/songs", name="/playlists/1/songs")

        @task(2)
        def list_playlists_containing_song(self):
            self.client.get("/playlists/search?songId=1", name="/playlists/search?songId=1")

if ACTIVE_SERVICES.get("soap"):
    class SoapApiUser(HttpUser):

        host = HOSTS["soap"]
        wait_time = between(1, 2)
        headers = {'Content-Type': 'text/xml'}

        def send_soap(self, request_name, inner_xml):
            payload = f"""<?xml version="1.0" encoding="UTF-8"?>
            <soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" 
                              xmlns:demo="http://example.com/demo">
                <soapenv:Header/>
                <soapenv:Body>
                    <demo:{request_name}>
                        {inner_xml}
                    </demo:{request_name}>
                </soapenv:Body>
            </soapenv:Envelope>"""
            self.client.post("/ws", data=payload, headers=self.headers, name=f"SOAP: {request_name}")

        @task(1)
        def list_users(self): 
            self.send_soap("getAllUsersRequest", "")

        @task(1)
        def list_songs(self): 
            self.send_soap("getAllSongsRequest", "")

        @task(2)
        def user_playlists(self):
            self.send_soap(
                "getUserPlaylistsRequest",
                "<demo:userId>1</demo:userId>"
            ) 
      
        @task(2)     
        def playlist_songs(self):
            self.send_soap(
                "getPlaylistSongsRequest",
                "<demo:playlistId>1</demo:playlistId>"
            ) 

        @task(2)
        def playlists_by_song(self):
            self.send_soap(
                "getPlaylistsBySongRequest",
                "<demo:songId>1</demo:songId>"
            )

if ACTIVE_SERVICES.get("graphql"):
    class GraphqlApiUser(HttpUser):

        host = HOSTS["graphql"]
        wait_time = between(1, 2)

        def run_query(self, name, query):
            self.client.post("/graphql", json={"query": query}, name=f"GQL: {name}")

        @task(1)
        def list_users(self):
            self.run_query("List Users", "{ users { id name } }")

        @task(1)
        def list_songs(self):
            self.run_query("List Songs", "{ songs { id title } }")

        @task(2)
        def user_playlists(self):
            self.run_query("User Playlists", "{ userPlaylists(userId: 1) { id name } }")

        @task(2)
        def playlist_songs(self):
            self.run_query("Playlist Songs", "{ playlistSongs(playlistId: 1) { id title } }")

        @task(2)
        def playlists_by_song(self):
            self.run_query("Playlists by Song", "{ playlistsBySong(songId: 1) { id name } }")

if ACTIVE_SERVICES.get("grpc"):
    class GrpcApiUser(User):
        host = HOSTS["grpc"]
        wait_time = between(1, 2)

        def record_metrics(self, name, start_time, response=None, exception=None):
            total_ms = int((time.time() - start_time) * 1000)
            events.request.fire(
                request_type="gRPC",
                name=name,
                response_time=total_ms,
                response_length=0 if not response else len(response.SerializeToString()),
                exception=exception
            )

        def on_start(self):
            self.address = HOSTS["grpc"]
            self.channel = grpc.insecure_channel(self.address)
            self.stub = demo_pb2_grpc.UserServiceStub(self.channel)

        @task(1)
        def get_all_users(self):
            start = time.time()
            try:
                response = self.stub.GetAllUsers(demo_pb2.Empty())
                self.record_metrics("GetAllUsers", start, response=response)
            except grpc.RpcError as e:
                self.record_metrics("GetAllUsers", start, exception=e)
        
        @task(1)
        def get_all_songs(self):
            start = time.time()
            try:
                response = self.stub.GetAllSongs(demo_pb2.Empty())
                self.record_metrics("GetAllSongs", start, response=response)
            except grpc.RpcError as e:
                self.record_metrics("GetAllSongs", start, exception=e)
        
        @task(2)
        def get_user_playlists(self):
            uid = 1
            start = time.time()
            try:
                response = self.stub.GetUserPlaylists(demo_pb2.IdRequest(id=uid))
                self.record_metrics("GetUserPlaylists", start, response=response)
            except grpc.RpcError as e:
                self.record_metrics("GetUserPlaylists", start, exception=e)
        
        @task(2)
        def get_playlist_songs(self):
            pid = 1
            start = time.time()
            try:
                response = self.stub.GetPlaylistSongs(demo_pb2.IdRequest(id=pid))
                self.record_metrics("GetPlaylistSongs", start, response=response)
            except grpc.RpcError as e:
                self.record_metrics("GetPlaylistSongs", start, exception=e)
        
        @task(2)
        def get_playlists_by_song(self):
            sid = 1
            start = time.time()
            try:
                response = self.stub.GetPlaylistsBySong(demo_pb2.IdRequest(id=sid))
                self.record_metrics("GetPlaylistsBySong", start, response=response)
            except grpc.RpcError as e:
                self.record_metrics("GetPlaylistsBySong", start, exception=e)
        
        def on_stop(self):
            self.channel.close()
