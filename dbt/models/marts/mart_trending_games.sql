-- Games ranked by 7-snapshot rolling average growth in concurrent players
with metrics as (
    select * from {{ ref('fact_game_metrics') }}
),

rolling as (
    select
        appid,
        snapshot_at,
        concurrent_players,
        rank,
        pct_change_players,
        rank_change,
        avg(concurrent_players) over (
            partition by appid
            order by snapshot_at
            rows between 20 preceding and current row  -- ~7 days at 8h intervals
        ) as rolling_7d_avg_players,
        avg(pct_change_players) over (
            partition by appid
            order by snapshot_at
            rows between 20 preceding and current row
        ) as rolling_7d_avg_growth
    from metrics
),

latest_snapshot as (
    select max(snapshot_at) as max_ts from metrics
),

final as (
    select
        r.appid,
        r.snapshot_at,
        r.concurrent_players,
        r.rank,
        r.pct_change_players,
        r.rank_change,
        r.rolling_7d_avg_players,
        r.rolling_7d_avg_growth,
        dense_rank() over (
            order by r.rolling_7d_avg_growth desc nulls last
        ) as trend_rank
    from rolling r
    inner join latest_snapshot l on r.snapshot_at = l.max_ts
)

select * from final
order by trend_rank
