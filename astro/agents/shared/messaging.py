"""Inter-agent messaging hooks (extend for pub/sub or Kafka)."""


def emit_event(topic: str, payload: dict) -> None:
    pass
