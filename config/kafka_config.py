from confluent_kafka.admin import AdminClient, NewTopic

from config.settings import KAFKA_BOOTSTRAP_SERVERS, KAFKA_RAW_TOPIC


def ensure_kafka_topic(topic_name: str = KAFKA_RAW_TOPIC, bootstrap_servers: str = KAFKA_BOOTSTRAP_SERVERS):
    admin_client = AdminClient({"bootstrap.servers": bootstrap_servers})
    metadata = admin_client.list_topics(timeout=5)
    existing_topics = set(metadata.topics.keys())

    if topic_name in existing_topics:
        return

    new_topic = NewTopic(topic=topic_name, num_partitions=1, replication_factor=1)
    fs = admin_client.create_topics([new_topic])

    for topic, future in fs.items():
        try:
            future.result(timeout=15)
            print(f"[Kafka] Topic created: {topic}")
        except Exception as exc:
            print(f"[Kafka] Could not create topic {topic}: {exc}")