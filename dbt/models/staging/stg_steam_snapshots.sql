-- Flattens raw JSON: one row per game per snapshot
with source as (
    select * from {{ source('raw', 'raw_steam_snapshots') }}
),

flattened as (
    select
        to_timestamp(raw_json:response:last_update::int)   as snapshot_at,
        game.value:appid::int                              as appid,
        game.value:rank::int                               as rank,
        game.value:concurrent_in_game::int                 as concurrent_players,
        game.value:peak_in_game::int                       as peak_players,
        loaded_at
    from source,
    lateral flatten(input => raw_json:response:ranks)      as game
)

select * from flattened
