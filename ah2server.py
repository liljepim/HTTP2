import asyncio
import json

import h2.config
import h2.connection
import h2.events

# from payload_generator import generate_payload


def send_response(conn, event):
    stream_id = event.stream_id
    response_data = json.dumps(
        {k.decode("utf-8"): v.decode("utf-8") for k, v in event.headers}
    ).encode("utf-8")

    # response_data = json.dumps(generate_payload()).encode("utf-8")

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


def handle_request(method, path, body):
    """
    Handle client requests and returns the response data to be sent to client

    Args:
        method (str): GET or POST
        path (str): Path requested e.g. /sensor, /alert
        body: request body in byte-like format

    Return(s):
        dict: Response data to send to client
        int: Response code (200:OK, 400: Bad Request)
    """

    # Handle Post Requests

    if method == "POST":
        if path == "/sensor":  # Received sensor data from sensor nodes
            try:
                data = json.loads(body.decode("utf-8"))
                print(f"Received Sensor Data: {data}")
                return (
                    {"status": "Sensor data received", "data": data},
                    200,
                )  # Echo data to client (only for debugging, can be omitted to maximize performance)
            except Exception as e:
                return {"error": f"Invalid JSON: {str(e)}"}, 400
        elif path == "/alert":
            try:
                data = json.loads(body.decode("utf-8"))
                print(f"Received Alert Data: {data}")
                return (
                    {"status": "Alert data received", "data": data},
                    200,
                )  # Echo data to client (only for debugging, can be omitted to maximize performance)
            except Exception as e:
                return {"error": f"Invalid JSON: {str(e)}"}, 400
    else:
        return {"error", "Not Found"}, 404


async def handle_client(reader, writer):
    config = h2.config.H2Configuration(client_side=False, header_encoding="utf-8")
    conn = h2.connection.H2Connection(config=config)
    conn.initiate_connection()
    writer.write(conn.data_to_send())
    await writer.drain()
    print(writer.get_extra_info("socket"))

    streams = {}

    while True:
        data = await reader.read(65535)
        if not data:
            break

        events = conn.receive_data(data)
        for event in events:
            if isinstance(event, h2.events.RequestReceived):
                headers = dict(event.headers)
                method = headers.get(":method")
                path = headers.get(":path")
                streams[event.stream_id] = {"body": b"", "method": method, "path": path}

            elif isinstance(event, h2.events.DataReceived):
                streams[event.stream_id]["body"] += event.data
                conn.acknowledge_received_data(
                    event.flow_controlled_length, event.stream_id
                )

            elif isinstance(event, h2.events.StreamEnded):
                req = streams.pop(event.stream_id)
                method, path, body = req["method"], req["path"], req["body"]

                payload, status = handle_request(method, path, body)
                response = json.dumps(payload).encode("utf-8")

                conn.send_headers(
                    event.stream_id,
                    headers=[
                        (":status", str(status)),
                        ("content-type", "application/json"),
                        ("content-length", str(len(response))),
                    ],
                )
                conn.send_data(event.stream_id, response, end_stream=True)

        writer.write(conn.data_to_send())
        await writer.drain()


async def main():
    server = await asyncio.start_server(handle_client, "0.0.0.0", 8080)
    addr = server.sockets[0].getsockname()
    print(f"Serving HTTP/2 on {addr}")

    async with server:
        await server.serve_forever()


if __name__ == "__main__":
    asyncio.run(main())
