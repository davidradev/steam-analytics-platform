with metrics as (
    select * from {{ ref('fact_game_metrics') }}
),

rolling as (
    select
        appid,
        snapshot_at,
        concurrent_players,
        rank,
        avg(concurrent_players) over (
            partition by appid
            order by snapshot_at
            rows between 20 preceding and current row
        ) as rolling_7d_avg_players
    from metrics
),

growth as (
    select
        *,
        lag(rolling_7d_avg_players) over (
            partition by appid
            order by snapshot_at
        ) as prev_rolling_7d_avg_players
    from rolling
),

latest_snapshot as (
    select max(snapshot_at) as max_ts from metrics
),

final as (
    select
        g.appid,
        g.snapshot_at,
        g.concurrent_players,
        g.rank,
        g.rolling_7d_avg_players,
        {{ pct_change('g.rolling_7d_avg_players', 'g.prev_rolling_7d_avg_players') }} as rolling_7d_avg_growth,
        dense_rank() over (
            order by {{ pct_change('g.rolling_7d_avg_players', 'g.prev_rolling_7d_avg_players') }} desc nulls last
        ) as trend_rank
    from growth g
    inner join latest_snapshot l on g.snapshot_at = l.max_ts
)

select * from final
order by trend_rank
