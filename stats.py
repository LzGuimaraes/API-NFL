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
    """Busca estatísticas dos times (wins/losses)"""
    season = get_current_season()
    url = f"https://site.api.espn.com/apis/site/v2/sports/football/nfl/standings?season={season}"
    
    try:
        resp = requests.get(url, timeout=15)
        if resp.status_code != 200:
            print(f"Erro na API standings: {resp.status_code}")
            return {}
        
        data = resp.json()
        team_standings = {}
        
        # Navega pela nova estrutura da API
        children = data.get("children", [])
        for conference in children:  # AFC/NFC
            standings = conference.get("standings", {}).get("entries", [])
            
            for entry in standings:
                team_info = entry.get("team", {})
                team_id = team_info.get("id")
                team_name = team_info.get("displayName")
                team_abbr = team_info.get("abbreviation")
                
                # Extrai wins/losses
                stats = entry.get("stats", [])
                wins = losses = 0
                
                for stat in stats:
                    stat_name = stat.get("name", "").lower()
                    if "wins" in stat_name or stat_name == "w":
                        wins = int(stat.get("value", 0))
                    elif "losses" in stat_name or stat_name == "l":
                        losses = int(stat.get("value", 0))
                
                # Armazena por ID, nome e abreviação para melhor correspondência
                team_standings[team_id] = {
                    'name': team_name,
                    'abbreviation': team_abbr,
                    'wins': wins,
                    'losses': losses
                }
        
        return team_standings
        
    except Exception as e:
        print(f"Erro ao buscar standings: {e}")
        return {}

def fetch_top_players():
    """Busca os jogadores líderes da liga"""
    season = get_current_season()
    url = f"https://site.api.espn.com/apis/site/v2/sports/football/nfl/leaders"
    
    try:
        resp = requests.get(url, timeout=10)
        if resp.status_code != 200:
            print(f"Erro na API leaders: {resp.status_code}")
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
                        'id': athlete.get('id'),
                        'name': athlete.get('displayName'),
                        'points': leader.get('value', 0)
                    })
        
        return top_players
        
    except Exception as e:
        print(f"Erro ao buscar líderes: {e}")
        return []

def update_stats_in_db():
    """Atualiza as estatísticas dos times e jogadores no banco"""
    db = SessionLocal()
    
    print("Atualizando estatísticas dos times...")
    team_standings = fetch_team_standings()
    
    teams_updated = 0
    for team_id, stats in team_standings.items():
        # Busca por ID (mais confiável)
        team = db.query(Team).filter(Team.id == int(team_id)).first()
        
        # Se não encontrar por ID, tenta por nome
        if not team:
            team = db.query(Team).filter(Team.name == stats['name']).first()
        
        # Se não encontrar por nome, tenta por abreviação
        if not team:
            team = db.query(Team).filter(Team.abbreviation == stats['abbreviation']).first()
        
        if team:
            team.wins = stats['wins']
            team.losses = stats['losses']
            teams_updated += 1
            print(f"  ✓ {team.name}: {stats['wins']}W - {stats['losses']}L")
        else:
            print(f"  ✗ Time não encontrado: {stats['name']} (ID: {team_id})")
    
    print(f"\nAtualizando pontos dos jogadores...")
    top_players = fetch_top_players()
    
    players_updated = 0
    for pdata in top_players:
        # Busca por ID (mais confiável)
        player = db.query(Player).filter(Player.id == int(pdata['id'])).first()
        
        # Se não encontrar por ID, tenta por nome
        if not player:
            player = db.query(Player).filter(Player.full_name == pdata['name']).first()
        
        if player:
            player.points = int(float(pdata['points']))
            players_updated += 1
            print(f"  ✓ {player.full_name}: {player.points} pontos")
    
    # Recalcula os pontos totais de cada time baseado nos seus jogadores
    print(f"\nRecalculando pontos dos times...")
    all_teams = db.query(Team).all()
    for team in all_teams:
        # Soma os pontos dos top 5 jogadores
        top_5_players = db.query(Player).filter(
            Player.team_id == team.id
        ).order_by(Player.points.desc()).limit(5).all()
        
        team.points = sum(p.points for p in top_5_players)
        print(f"  ✓ {team.name}: {team.points} pontos totais")
    
    db.commit()
    db.close()
    
    print(f"\n✅ Atualização concluída!")
    print(f"   - {teams_updated} times atualizados")
    print(f"   - {players_updated} jogadores atualizados")