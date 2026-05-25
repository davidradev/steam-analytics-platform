{{
    config(
        materialized = 'incremental',
        unique_key   = ['appid', 'snapshot_at'],
        on_schema_change = 'sync_all_columns'
    )
}}

with source as (
    select * from {{ ref('stg_steam_snapshots') }}

    {% if is_incremental() %}
        where snapshot_at > (select max(snapshot_at) from {{ this }})
    {% endif %}
),

with_prev as (
    select
        snapshot_at,
        appid,
        rank,
        concurrent_players,
        peak_players,
        lag(concurrent_players) over (
            partition by appid
            order by snapshot_at
        ) as prev_concurrent_players,
        lag(rank) over (
            partition by appid
            order by snapshot_at
        ) as prev_rank
    from source
)

select
    snapshot_at,
    appid,
    rank,
    concurrent_players,
    peak_players,
    prev_concurrent_players,
    prev_rank,
    {{ pct_change('concurrent_players', 'prev_concurrent_players') }} as pct_change_players,
    (prev_rank - rank)                                                as rank_change
from with_prev
