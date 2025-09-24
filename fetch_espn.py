import requests
from sqlalchemy.orm import Session
from db import SessionLocal, Base, engine
from models import Team, Player

Base.metadata.create_all(bind=engine)

NFL_TEAMS_URL = "https://site.api.espn.com/apis/site/v2/sports/football/nfl/teams"

def fetch_and_store_data():
    db: Session = SessionLocal()

    resp = requests.get(NFL_TEAMS_URL)
    teams_data = resp.json().get("sports", [])[0].get("leagues", [])[0].get("teams", [])

    for team_entry in teams_data:
        team_info = team_entry.get("team", {})
        team = Team(
            id=int(team_info.get("id")),
            name=team_info.get("displayName"),
            abbreviation=team_info.get("abbreviation")
        )
        db.merge(team)
        db.commit()

        roster_url = f"https://site.api.espn.com/apis/site/v2/sports/football/nfl/teams/{team.id}/roster"
        roster_resp = requests.get(roster_url).json()

        entries = roster_resp.get("entries", [])[:5]  # só os 5 principais

        for entry in entries:
            player_ref = entry.get("player", {}).get("$ref")
            if not player_ref:
                continue

            player_resp = requests.get(player_ref + "/bio").json()
            athlete = player_resp.get("athlete")
            if not athlete or not athlete.get("id"):
                continue

            db.merge(Player(
                id=int(athlete.get("id")),
                full_name=athlete.get("displayName"),
                position=athlete.get("position", {}).get("abbreviation"),
                jersey=athlete.get("jersey"),
                height=athlete.get("height"),
                weight=athlete.get("weight"),
                date_of_birth=athlete.get("dateOfBirth"),
                age=athlete.get("age"),
                college=(athlete.get("college") or {}).get("name"),
                team_id=team.id
            ))

        db.commit()

    db.close()
    print("✅ Dados importados com sucesso!")
