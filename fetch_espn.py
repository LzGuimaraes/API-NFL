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

def fetch_team_record(session, team_id):
    """Busca o record (wins/losses) de um time específico"""
    try:
        url = f"https://site.api.espn.com/apis/site/v2/sports/football/nfl/teams/{team_id}"
        resp = session.get(url, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            team = data.get("team", {})
            record = team.get("record", {}).get("items", [])
            
            wins = 0
            losses = 0
            
            for item in record:
                if item.get("type") == "total":
                    stats = item.get("stats", [])
                    for stat in stats:
                        if stat.get("name") == "wins":
                            wins = int(stat.get("value", 0))
                        elif stat.get("name") == "losses":
                            losses = int(stat.get("value", 0))
                    break
            
            return wins, losses
    except Exception as e:
        print(f"Erro ao buscar record do time {team_id}: {e}")
    
    return 0, 0

def fetch_player_stats(session, athlete_id):
    """Busca estatísticas detalhadas de um jogador"""
    season = get_current_season()
    headers = {'User-Agent': 'Mozilla/5.0'}
    
    # Tenta múltiplas URLs e métodos para pegar pontos
    urls_to_try = [
        f"https://sports.core.api.espn.com/v2/sports/football/leagues/nfl/seasons/{season}/types/2/athletes/{athlete_id}/statistics/0",
        f"https://site.api.espn.com/apis/site/v2/sports/football/nfl/athletes/{athlete_id}/statistics",
        f"https://site.api.espn.com/apis/common/v3/sports/football/nfl/athletes/{athlete_id}/statistics",
    ]
    
    for url in urls_to_try:
        try:
            resp = session.get(url, headers=headers, timeout=8)
            if resp.status_code != 200:
                continue
            
            data = resp.json()
            points = 0
            
            # Método 1: Procura em splits/categories
            if "splits" in data:
                categories = data.get("splits", {}).get("categories", [])
                for category in categories:
                    stats = category.get("stats", [])
                    for stat in stats:
                        stat_name = stat.get("name", "").lower()
                        # Procura por fantasy points, total points, ou scoring
                        if any(keyword in stat_name for keyword in ["fantasy", "total points", "scoring"]):
                            points = max(points, float(stat.get("value", 0)))
            
            # Método 2: Procura em stats direto
            if points == 0 and "statistics" in data:
                stats = data.get("statistics", {})
                if isinstance(stats, dict):
                    for key, value in stats.items():
                        if "fantasy" in key.lower() or "points" in key.lower():
                            try:
                                points = max(points, float(value))
                            except:
                                pass
            
            # Método 3: Calcula pontos baseado em estatísticas básicas
            if points == 0 and "splits" in data:
                categories = data.get("splits", {}).get("categories", [])
                for category in categories:
                    stats = category.get("stats", [])
                    stats_dict = {s.get("name", "").lower(): float(s.get("value", 0)) for s in stats}
                    
                    # Cálculo aproximado de fantasy points
                    passing_yards = stats_dict.get("passingyards", 0)
                    passing_tds = stats_dict.get("passingtouchdowns", 0)
                    rushing_yards = stats_dict.get("rushingyards", 0)
                    rushing_tds = stats_dict.get("rushingtouchdowns", 0)
                    receiving_yards = stats_dict.get("receivingyards", 0)
                    receiving_tds = stats_dict.get("receivingtouchdowns", 0)
                    receptions = stats_dict.get("receptions", 0)
                    
                    calculated_points = (
                        (passing_yards * 0.04) +
                        (passing_tds * 4) +
                        (rushing_yards * 0.1) +
                        (rushing_tds * 6) +
                        (receiving_yards * 0.1) +
                        (receiving_tds * 6) +
                        (receptions * 0.5)
                    )
                    
                    points = max(points, calculated_points)
            
            if points > 0:
                return int(points)
                
        except Exception as e:
            continue
    
    return 0

def fetch_and_store_data():
    db: Session = SessionLocal()
    session = requests.Session()

    print("Buscando times da NFL...")
    resp = session.get(NFL_TEAMS_URL, timeout=10)
    teams_data = resp.json().get("sports", [])[0].get("leagues", [])[0].get("teams", [])

    for team_entry in teams_data:
        team_info = team_entry.get("team", {})
        team_id = int(team_info.get("id"))
        team_name = team_info.get("displayName")
        
        print(f"\n{'='*60}")
        print(f"Time: {team_name}")
        print(f"{'='*60}")
        
        # Busca wins e losses do time
        wins, losses = fetch_team_record(session, team_id)
        
        team = Team(
            id=team_id,
            name=team_name,
            abbreviation=team_info.get("abbreviation"),
            wins=wins,
            losses=losses,
            points=0  # Será calculado depois baseado nos jogadores
        )
        db.merge(team)
        db.commit()
        
        print(f"Record: {wins}W - {losses}L")

        roster_url = f"https://site.api.espn.com/apis/site/v2/sports/football/nfl/teams/{team_id}/roster"
        roster_resp = session.get(roster_url, timeout=10).json()
        athletes_groups = roster_resp.get("athletes", [])

        players_list = []
        athlete_ids = []
        athlete_map = {}

        for group in athletes_groups:
            items = group.get("items", [])
            for athlete in items[:15]:  # Pega 15 para garantir que teremos top 5 com pontos
                athlete_id = athlete.get("id")
                if athlete_id:
                    athlete_ids.append(athlete_id)
                    athlete_map[athlete_id] = athlete

        print(f"Buscando estatísticas de {len(athlete_ids)} jogadores...")

        # busca stats em paralelo
        with ThreadPoolExecutor(max_workers=10) as executor:
            future_to_id = {executor.submit(fetch_player_stats, session, aid): aid for aid in athlete_ids}
            for future in as_completed(future_to_id):
                aid = future_to_id[future]
                try:
                    points = future.result()
                except:
                    points = 0
                
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
                    "points": points
                })

        # pega top 5
        top_players = sorted(players_list, key=lambda x: x["points"], reverse=True)[:5]
        
        # Calcula pontos totais do time (soma dos top 5)
        team_total_points = sum(p["points"] for p in top_players)
        
        print(f"\nTop 5 jogadores:")
        for i, p in enumerate(top_players, 1):
            db.merge(Player(**p))
            print(f"  {i}. {p['full_name']} ({p['position']}) - {p['points']} pontos")
        
        # Atualiza os pontos do time
        team_obj = db.query(Team).filter(Team.id == team_id).first()
        if team_obj:
            team_obj.points = team_total_points
        
        db.commit()
        print(f"\n✓ Total de pontos do time: {team_total_points}")

    db.close()
    session.close()
    print(f"\n{'='*60}")
    print("✅ Dados importados com sucesso!")
    print(f"{'='*60}")