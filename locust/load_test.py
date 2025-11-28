import time
import grpc
import os
from locust import HttpUser, User, task, between, events
import demo_pb2
import demo_pb2_grpc

try:
    from grpc_tools import protoc
    protoc.main((
        '',
        '-I.',
        '--python_out=.',
        '--grpc_python_out=.',
        'demo.proto',
    ))
    import demo_pb2
    import demo_pb2_grpc
    GRPC_AVAILABLE = True
except Exception as e:
    print(f"gRPC generation failed (proto file missing?): {e}")
    GRPC_AVAILABLE = False

class RestApiUser(HttpUser):
    host = "http://rest-api:8080"
    wait_time = between(1, 2)

    @task
    def get_users(self):
        self.client.get("/users")

    @task
    def create_user(self):
        self.client.post("/users", json={"name": "LoadTest", "email": "load@test.com"})

class SoapApiUser(HttpUser):
    host = "http://soap-api:8080"
    wait_time = between(1, 2)

    @task
    def get_user_soap(self):
        payload = """
        <soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:demo="http://example.com/demo">
           <soapenv:Header/>
           <soapenv:Body>
              <demo:getUserRequest>
                 <demo:id>1</demo:id>
              </demo:getUserRequest>
           </soapenv:Body>
        </soapenv:Envelope>
        """
        headers = {'Content-Type': 'text/xml'}
        self.client.post("/ws", data=payload, headers=headers, name="SOAP GetUser")

class GraphqlApiUser(HttpUser):
    host = "http://graphql-api:8000"
    wait_time = between(1, 2)

    @task
    def query_deep_data(self):
        query = """
        query {
            users {
                name
                playlists {
                    title
                    songs {
                        title
                        artist
                    }
                }
            }
        }
        """
        self.client.post("/graphql", json={"query": query}, name="GraphQL Deep Query")

class GrpcApiUser(User):
    wait_time = between(1, 2)

    def on_start(self):
        self.channel = grpc.insecure_channel("grpc-api:50051")
        self.stub = demo_pb2_grpc.UserServiceStub(self.channel)

    @task
    def get_user_grpc(self):
        start_time = time.time()
        try:
            response = self.stub.GetUser(demo_pb2.UserRequest(id=1))
            total_ms = (time.time() - start_time) * 1000
            events.request.fire(
                request_type="gRPC",
                name="GetUser",
                response_time=total_ms,
                response_length=len(response.SerializeToString()),
                exception=None
            )
        except grpc.RpcError as e:
            total_ms = (time.time() - start_time) * 1000
            events.request.fire(
                request_type="gRPC",
                name="GetUser",
                response_time=total_ms,
                response_length=0,
                exception=e
            )

    def on_stop(self):
        self.channel.close()
