import json
import socket
import time

import h2.config
import h2.connection
import h2.events

from payload_generator import generate_payload


def establish_connection(sock):
    config = h2.config.H2Configuration(client_side=True, header_encoding="utf-8")
    conn = h2.connection.H2Connection(config=config)

    conn.initiate_connection()
    sock.sendall(conn.data_to_send())
    return conn


def post_http(sock, conn):
    body = json.dumps(generate_payload()).encode("utf-8")

    # Send POST headers
    stream_id = conn.get_next_available_stream_id()
    headers = [
        (":method", "POST"),
        (":authority", "0.0.0.0:8080"),
        (":scheme", "http"),
        (":path", "/alert"),
        ("content-type", "application/json"),
        ("content-length", str(len(body))),
    ]
    conn.send_headers(stream_id, headers, end_stream=False)
    sock.sendall(conn.data_to_send())

    conn.send_data(stream_id, body, end_stream=True)
    sock.sendall(conn.data_to_send())

    response_body = b""

    while True:
        data = sock.recv(65535)
        if not data:
            break

        events = conn.receive_data(data)
        for event in events:
            if isinstance(event, h2.events.ResponseReceived):
                print("Response Headers: ", dict(event.headers))
            elif isinstance(event, h2.events.DataReceived):
                response_body += event.data
                conn.acknowledge_received_data(
                    event.flow_controlled_length, event.stream_id
                )
            elif isinstance(event, h2.events.StreamEnded):
                print(response_body.decode("utf-8", errors="ignore"))
                return


def get_http(sock, conn):
    stream_id = conn.get_next_available_stream_id()
    headers = [
        (":method", "get"),
        (":authority", "0.0.0.0"),
        (":scheme", "http"),
        (":path", "/"),
    ]
    conn.send_headers(stream_id, headers, end_stream=True)
    sock.sendall(conn.data_to_send())

    body = b""
    while True:
        data = sock.recv(65535)
        if not data:
            break

        events = conn.receive_data(data)
        for event in events:
            if isinstance(event, h2.events.ResponseReceived):
                print("Response Headers: ", dict(event.headers))
            elif isinstance(event, h2.events.DataReceived):
                body += event.data
                conn.acknowledge_received_data(
                    event.flow_controlled_length, event.stream_id
                )
            elif isinstance(event, h2.events.StreamEnded):
                print(body.decode("utf-8", errors="ignore"))
                return


def main():
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect(("0.0.0.0", 8080))
        conn = establish_connection(sock)
        while True:
            post_http(sock, conn)
            time.sleep(1)
    except KeyboardInterrupt:
        print("Terminating HTTP/2 Client program")
        sock.close()
    except Exception as e:
        print(e)


if __name__ == "__main__":
    main()
