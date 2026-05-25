import os
import json
import time
import requests
from dotenv import load_dotenv
import snowflake.connector
from azure.storage.blob import BlobServiceClient, ContentSettings

load_dotenv()

SNOWFLAKE_ACCOUNT   = os.getenv("SNOWFLAKE_ACCOUNT")
SNOWFLAKE_USER      = os.getenv("SNOWFLAKE_USER")
SNOWFLAKE_PASSWORD  = os.getenv("SNOWFLAKE_PASSWORD")
AZURE_CONN_STR      = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
PUBLIC_CONTAINER    = "steam-public"

def get_snowflake_connection():
    return snowflake.connector.connect(
        account   = SNOWFLAKE_ACCOUNT,
        user      = SNOWFLAKE_USER,
        password  = SNOWFLAKE_PASSWORD,
        database  = "STEAM_DW",
        warehouse = "STEAM_WH",
    )

def fetch_game_names(appids):
    names = {}
    for appid in appids:
        try:
            r = requests.get(
                "https://store.steampowered.com/api/appdetails",
                params={"appids": str(appid), "filters": "basic"},
                timeout=10
            )
            entry = r.json().get(str(appid), {})
            if entry.get("success") and entry.get("data"):
                names[appid] = entry["data"].get("name", str(appid))
            else:
                names[appid] = str(appid)
        except Exception:
            names[appid] = str(appid)
        time.sleep(0.5)  # avoid Steam rate limiting
    return names

def query_to_list(cursor, sql):
    cursor.execute(sql)
    cols = [d[0].lower() for d in cursor.description]
    return [dict(zip(cols, row)) for row in cursor.fetchall()]

def upload_json(blob_client, data, blob_name):
    payload = json.dumps(data, default=str)
    blob_client.get_blob_client(blob_name).upload_blob(
        payload,
        overwrite=True,
        content_settings=ContentSettings(content_type="application/json")
    )
    print(f"Uploaded: {blob_name}")

def main():
    conn       = get_snowflake_connection()
    cursor     = conn.cursor()
    blob_svc   = BlobServiceClient.from_connection_string(AZURE_CONN_STR)
    container  = blob_svc.get_container_client(PUBLIC_CONTAINER)

    top_games = query_to_list(cursor, """
        SELECT appid, rank, concurrent_players, peak_players, pct_change_players, rank_change
        FROM STEAM_DW.STAGING_MARTS.MART_TOP_GAMES_CURRENT
        ORDER BY rank
        LIMIT 20
    """)
    all_appids = [g["appid"] for g in top_games]
    names = fetch_game_names(all_appids)
    for g in top_games:
        g["name"] = names.get(g["appid"], str(g["appid"]))
    upload_json(container, top_games, "top_games_current.json")

    trending = query_to_list(cursor, """
        SELECT appid, concurrent_players, rolling_7d_avg_players,
               rolling_7d_avg_growth, trend_rank, pct_change_players
        FROM STEAM_DW.STAGING_MARTS.MART_TRENDING_GAMES
        ORDER BY trend_rank
        LIMIT 20
    """)
    for g in trending:
        g["name"] = names.get(g["appid"], str(g["appid"]))
    upload_json(container, trending, "trending_games.json")

    history = query_to_list(cursor, """
        SELECT appid, snapshot_at, concurrent_players
        FROM STEAM_DW.STAGING_CORE.FACT_GAME_METRICS
        WHERE appid IN (
            SELECT appid FROM STEAM_DW.STAGING_MARTS.MART_TOP_GAMES_CURRENT
            ORDER BY rank LIMIT 5
        )
        ORDER BY appid, snapshot_at
    """)
    for row in history:
        row["name"] = names.get(row["appid"], str(row["appid"]))
    upload_json(container, history, "player_history.json")

    cursor.close()
    conn.close()
    print("Export complete.")

if __name__ == "__main__":
    main()
