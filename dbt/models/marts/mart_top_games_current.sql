-- Current snapshot ranking with historical context
with latest as (
    select max(snapshot_at) as max_ts
    from {{ ref('fact_game_metrics') }}
),

current_snapshot as (
    select
        f.appid,
        f.snapshot_at,
        f.rank,
        f.concurrent_players,
        f.peak_players,
        f.pct_change_players,
        f.rank_change
    from {{ ref('fact_game_metrics') }} f
    inner join latest l on f.snapshot_at = l.max_ts
)

select * from current_snapshot
order by rank
