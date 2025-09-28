import datetime
import json
import random
import socket

import h2.config
import h2.connection
import h2.events

message_counter = 1


def generate_message_id():
    global message_counter
    message_id = f"msg_{message_counter:04d}"
    message_counter += 1
    return message_id


def generate_payload(
    node_id="node_01",
    application_protocol=None,
    transport_protocol=None,
    packet_type="sensor_reading",
    sensor_type="combined_environmental",
    retransmission_count=0,
):
    app_protocols = ["CoAP", "HTTP", "MQTT"]
    transport_protocols = ["QUIC", "TCP", "UDP"]

    application_protocol = application_protocol or random.choice(app_protocols)
    transport_protocol = transport_protocol or random.choice(transport_protocols)

    payload = {
        "message_id": generate_message_id(),
        "timestamp": datetime.datetime.now().isoformat(),
        "node_id": node_id,
        "application_protocol": application_protocol,
        "transport_protocol": transport_protocol,
        "kb_estimate": round(random.uniform(0.75, 1.25), 2),
        "retransmission_count": retransmission_count,
        "sensor_readings": {
            "temperature": round(random.uniform(18.0, 35.0), 1),
            "soil_moisture": round(random.uniform(10.0, 60.0), 1),
            "humidity": round(random.uniform(30.0, 90.0), 1),
        },
        "packet_type": packet_type,
        "sensor_type": sensor_type,
    }

    return payload


def send_response(conn, event):
    stream_id = event.stream_id
    # response_data = json.dumps(
    #     {k.decode("utf-8"): v.decode("utf-8") for k, v in event.headers}
    # ).encode("utf-8")

    response_data = json.dumps(generate_payload()).encode("utf-8")

    conn.send_headers(
        stream_id=stream_id,
        headers=[
            (":status", "200"),
            ("server", "basic-h2-server/1.0"),
            ("content-length", str(len(response_data))),
            ("content-type", "application/json"),
        ],
    )
    conn.send_data(stream_id=stream_id, data=response_data, end_stream=True)


def handle(sock):
    config = h2.config.H2Configuration(client_side=False)
    conn = h2.connection.H2Connection(config=config)
    conn.initiate_connection()
    sock.sendall(conn.data_to_send())

    while True:
        data = sock.recv(65535)
        if not data:
            break

        events = conn.receive_data(data)
        for event in events:
            if isinstance(event, h2.events.RequestReceived):
                send_response(conn, event)

        data_to_send = conn.data_to_send()
        if data_to_send:
            sock.sendall(data_to_send)


sock = socket.socket()
sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
sock.bind(("0.0.0.0", 8080))
sock.listen(5)

while True:
    handle(sock.accept()[0])
