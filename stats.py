import requests
from db import SessionLocal
from models import Team, Player

def get_current_season():
    """Detecta a temporada atual"""
    try:
        url = "https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard"
        resp = requests.get(url, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            return data.get("season", {}).get("year", 2024)
    except:
        pass
    return 2024

def fetch_team_standings():
    season = get_current_season()
    url = f"https://site.api.espn.com/apis/site/v2/sports/football/nfl/standings?season={season}"
    
    try:
        resp = requests.get(url, timeout=15)
        if resp.status_code != 200:
            return {}
        
        data = resp.json()
        team_standings = {}
        
        # Navega pela nova estrutura da API
        children = data.get("children", [])
        for conference in children:  # AFC/NFC
            standings = conference.get("standings", {}).get("entries", [])
            
            for entry in standings:
                team_info = entry.get("team", {})
                team_name = team_info.get("displayName")
                
                # Extrai wins/losses
                stats = entry.get("stats", [])
                wins = losses = 0
                
                for stat in stats:
                    stat_name = stat.get("name", "").lower()
                    if "wins" in stat_name or stat_name == "w":
                        wins = int(stat.get("value", 0))
                    elif "losses" in stat_name or stat_name == "l":
                        losses = int(stat.get("value", 0))
                
                team_standings[team_name] = {
                    'wins': wins,
                    'losses': losses
                }
        
        return team_standings
        
    except Exception as e:
        print(f"Erro ao buscar standings: {e}")
        return {}

def fetch_top_players():
    season = get_current_season()
    url = f"https://site.api.espn.com/apis/site/v2/sports/football/nfl/leaders"
    
    try:
        resp = requests.get(url, timeout=10)
        if resp.status_code != 200:
            return []
        
        data = resp.json()
        top_players = []
        
        # Processa líderes
        categories = data.get("categories", [])
        for category in categories:
            leaders = category.get("leaders", [])
            for leader in leaders:
                athlete = leader.get("athlete", {})
                if athlete:
                    top_players.append({
                        'name': athlete.get('displayName'),
                        'points': leader.get('value', 0)
                    })
        
        return top_players
        
    except Exception as e:
        print(f"Erro ao buscar líderes: {e}")
        return []

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
            player.points = int(float(pdata['points']))

    db.commit()
    db.close()
    print("✅ Stats atualizados")