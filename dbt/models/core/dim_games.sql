-- Catalogue of unique games seen across all snapshots
with all_games as (
    select distinct appid
    from {{ ref('stg_steam_snapshots') }}
)

select
    appid,
    current_timestamp() as first_seen_at
from all_games
