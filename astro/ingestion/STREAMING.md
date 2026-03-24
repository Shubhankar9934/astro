# Streaming architecture

## Phase A (in-process, default)

- `asyncio.Queue` for bars (`MarketStream.queue`) and optional news (`NewsStream.queue`).
- `IngestionScheduler` runs IBKR real-time subscriptions and drains queues.
- Backpressure: queues are bounded; drop/coalesce in handlers if producers outpace consumers.

## Phase B (Kafka / Redpanda)

- Producers: `raw.bars`, `raw.news` topics with schema-versioned payloads (JSON Schema or Protobuf).
- Consumers: feature workers write `data/features/`, publish `features.fused`.
- Decision workers subscribe to `features.fused` and trigger `DecisionExecutor` with debouncing from `configs/system.yaml`.

Use Phase B when multiple services or languages must consume the same stream.
