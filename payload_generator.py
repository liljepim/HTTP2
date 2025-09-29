import datetime
import json
import random

# global msg counter
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


# sample
if __name__ == "__main__":
    for _ in range(5):
        payload = generate_payload()
        print(json.dumps(payload, indent=2))

