import requests
from sqlalchemy.orm import Session
from db import SessionLocal, Base, engine
from models import Team, Player
from concurrent.futures import ThreadPoolExecutor, as_completed

Base.metadata.create_all(bind=engine)

NFL_TEAMS_URL = "https://site.api.espn.com/apis/site/v2/sports/football/nfl/teams"

def get_current_season():
    try:
        url = "https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard"
        resp = requests.get(url, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            return data.get("season", {}).get("year", 2024)
    except:
        pass
    return 2024

def fetch_player_fantasy_points(session, athlete_id):
    season = get_current_season()
    urls_to_try = [
        f"https://sports.core.api.espn.com/v2/sports/football/leagues/nfl/seasons/{season}/types/2/athletes/{athlete_id}/statistics",
        f"https://site.api.espn.com/apis/site/v2/sports/football/nfl/athletes/{athlete_id}/stats"
    ]
    headers = {
        'User-Agent': 'Mozilla/5.0'
    }
    for url in urls_to_try:
        try:
            resp = session.get(url, headers=headers, timeout=8)
            if resp.status_code != 200:
                continue
            data = resp.json()
            
            # tenta pegar fantasy points direto
            fantasy_points = 0
            if "splits" in data:
                categories = data.get("splits", {}).get("categories", [])
                for category in categories:
                    for stat in category.get("stats", []):
                        if "fantasy" in stat.get("name", "").lower():
                            fantasy_points = float(stat.get("value", 0))
                            break
                    if fantasy_points > 0:
                        break
            if fantasy_points == 0 and "stats" in data:
                stats_list = data["stats"]
                if isinstance(stats_list, list):
                    for season_stats in stats_list:
                        for stat in season_stats.get("stats", []):
                            if "fantasy" in stat.get("name", "").lower():
                                fantasy_points = float(stat.get("value", 0))
                                break
            # se nada encontrado, retorna 0
            return fantasy_points
        except:
            continue
    return 0

def fetch_and_store_data():
    db: Session = SessionLocal()
    session = requests.Session()

    resp = session.get(NFL_TEAMS_URL, timeout=10)
    teams_data = resp.json().get("sports", [])[0].get("leagues", [])[0].get("teams", [])

    for team_entry in teams_data:
        team_info = team_entry.get("team", {})
        team_id = int(team_info.get("id"))
        team = Team(
            id=team_id,
            name=team_info.get("displayName"),
            abbreviation=team_info.get("abbreviation")
        )
        db.merge(team)
        db.commit()

        roster_url = f"https://site.api.espn.com/apis/site/v2/sports/football/nfl/teams/{team_id}/roster"
        roster_resp = session.get(roster_url, timeout=10).json()
        athletes_groups = roster_resp.get("athletes", [])

        players_list = []
        athlete_ids = []
        athlete_map = {}

        for group in athletes_groups:
            items = group.get("items", [])
            for athlete in items[:10]:  # limitar para 10 jogadores por grupo
                athlete_id = athlete.get("id")
                if athlete_id:
                    athlete_ids.append(athlete_id)
                    athlete_map[athlete_id] = athlete

        # busca fantasy points em paralelo
        with ThreadPoolExecutor(max_workers=10) as executor:
            future_to_id = {executor.submit(fetch_player_fantasy_points, session, aid): aid for aid in athlete_ids}
            for future in as_completed(future_to_id):
                aid = future_to_id[future]
                try:
                    fantasy_points = future.result()
                except:
                    fantasy_points = 0
                athlete = athlete_map[aid]

                position_info = athlete.get("position", {})
                position = position_info.get("abbreviation") if isinstance(position_info, dict) else str(position_info)

                college_name = None
                if athlete.get("college"):
                    college_info = athlete["college"]
                    if isinstance(college_info, dict):
                        college_name = college_info.get("name")
                    else:
                        college_name = str(college_info)

                players_list.append({
                    "id": int(aid),
                    "full_name": athlete.get("displayName"),
                    "position": position,
                    "jersey": athlete.get("jersey"),
                    "height": athlete.get("height"),
                    "weight": athlete.get("weight"),
                    "date_of_birth": athlete.get("dateOfBirth"),
                    "age": athlete.get("age"),
                    "college": college_name,
                    "team_id": team_id,
                    "points": fantasy_points
                })

        # pega top 5
        top_players = sorted(players_list, key=lambda x: x["points"], reverse=True)[:5]
        for p in top_players:
            db.merge(Player(**p))
        db.commit()

    db.close()
    session.close()
    print("✅ Dados importados com sucesso!")
