# Building Reliable Postgres Replication

## Why Replication Matters

Postgres replication is the backbone of any production database deployment.
Without it, you are one hardware failure away from a very bad day.

## Streaming vs Logical Replication

Streaming replication copies the entire WAL stream to a standby. It is simple
and battle-tested but gives you an exact physical copy — no filtering, no
transformation. Logical replication operates at the table level and lets you
select which tables to replicate, transform data, or even replicate between
different Postgres major versions.

## Common Pitfalls

Replication slots can fill your disk if a standby falls behind. Always monitor
`pg_stat_replication` and set `max_slot_wal_keep_size`. Connection drops during
heavy write loads can cause the standby to fall behind faster than it can catch
up — tune `wal_sender_timeout` and `max_wal_senders` accordingly.
