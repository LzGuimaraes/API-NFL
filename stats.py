import requests
from db import SessionLocal
from models import Team, Player

def fetch_team_standings():
    url = "https://sports.core.api.espn.com/v2/sports/football/leagues/nfl/seasons/2025/standings"
    resp = requests.get(url).json()
    team_standings = {}

    for team_entry in resp.get('teams', []):
        team_name = team_entry.get('team', {}).get('displayName')
        stats = {stat['name']: stat['value'] for stat in team_entry.get('stats', [])}
        team_standings[team_name] = {
            'wins': stats.get('wins', 0),
            'losses': stats.get('losses', 0)
        }
    return team_standings

def fetch_top_players():
    url = "https://sports.core.api.espn.com/v2/sports/football/leagues/nfl/leaders"
    resp = requests.get(url).json()
    top_players = []

    for player_entry in resp.get('leaders', []):
        athlete = player_entry.get('athlete')
        if athlete:
            top_players.append({
                'name': athlete.get('displayName'),
                'points': player_entry.get('value', 0)
            })
    return top_players

def update_stats_in_db():
    db = SessionLocal()

    team_standings = fetch_team_standings()
    for name, stats in team_standings.items():
        team = db.query(Team).filter(Team.name == name).first()
        if team:
            team.wins = stats['wins']
            team.losses = stats['losses']

    top_players = fetch_top_players()
    for pdata in top_players:
        player = db.query(Player).filter(Player.full_name == pdata['name']).first()
        if player:
            player.points = pdata['points']

    db.commit()
    db.close()
    print("✅ Stats atualizados")
