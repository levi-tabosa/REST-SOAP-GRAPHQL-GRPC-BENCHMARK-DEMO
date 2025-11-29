FROM locustio/locust

USER root

COPY . .
RUN pip install -r requirements.txt
RUN python -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. demo.proto
