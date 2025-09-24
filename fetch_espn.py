import requests
from sqlalchemy.orm import Session
from models import Team, Player
from db import SessionLocal, engine, Base

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
        db.merge(team)  # upsert
        db.commit()

        # Roster (lista de jogadores do time)
        roster_url = f"https://site.api.espn.com/apis/site/v2/sports/football/nfl/teams/{team.id}/roster"
        roster_resp = requests.get(roster_url).json()

        # ESPN já retorna ordenado → pegamos apenas os 5 principais
        players = roster_resp.get("athletes", [])[:5]

        for player in players:
            info = player.get("athlete", {})
            db.merge(Player(
                id=int(info.get("id")),
                full_name=info.get("displayName"),
                position=info.get("position", {}).get("abbreviation"),
                jersey=info.get("jersey"),
                height=info.get("height"),
                weight=info.get("weight"),
                date_of_birth=info.get("dateOfBirth"),
                age=info.get("age"),
                college=(info.get("college") or {}).get("name"),
                team_id=team.id
            ))

        db.commit()

    db.close()
