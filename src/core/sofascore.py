import time
import requests as rq

from typing import List, Dict, Any, Collection, Tuple
from core.common import DotDict, flatten

# ---------------------------- #

SOFASCORE_API = 'https://api.sofascore.com/api/v1'
HEADERS = {
    'Content-Type' : 'application/json'
}

# ---------------------------- #

def extract_one_page_events_tournament(tournament_id: int, season: int, page: int = 0, kind: str = 'next') -> Tuple[Collection[Dict[str, Any]], bool]:
    
    url = f"{SOFASCORE_API}/unique-tournament/{season}/season/{tournament_id}/events/{kind}/{page}"
    response = rq.get(url, headers=HEADERS)
    data = response.json()

    parsed_events = list(map(parse_event_data, data['events']))
    has_next_page = data['hasNextPage']

    return parsed_events, has_next_page

# ---------------------------- #

def extract_all_events_tournament_by_kind(

        tournament_id: int, 
        season: int, 
        kind: str = 'next',
        timeout: float = 0.08

    ) -> Collection[Dict[str, Any]]:
    
    parsed_events = []
    has_next_page = True
    page = 0

    while has_next_page:
        new_page_events, has_next_page = extract_one_page_events_tournament(
                                            tournament_id=tournament_id, 
                                            season=season,
                                            page=page,
                                            kind=kind
                                        )
        parsed_events += new_page_events
        page += 1
        time.sleep(timeout)
    
    return parsed_events

# ---------------------------- #

def extract_all_events_tournament(tournament_id: int, season: int) -> Collection[Dict[str, Any]]:

    ended_events = extract_all_events_tournament_by_kind(
                        tournament_id=tournament_id, 
                        season=season, 
                        kind='last'
                    )
    upcoming_events = extract_all_events_tournament_by_kind(
                        tournament_id=tournament_id, 
                        season=season, 
                        kind='next'
                    )

    return ended_events + upcoming_events

# ---------------------------- #

def extract_tournament_biweekly_data(tournament_id: int, season: int) -> Dict[str, Any]:

    url = f"{SOFASCORE_API}/unique-tournament/{season}/season/{tournament_id}/top-players/overall"
    response = rq.get(url, headers=HEADERS)
    top_players_data = response.json()

    url = f"{SOFASCORE_API}/unique-tournament/{season}/season/{tournament_id}/top-teams/overall"
    response = rq.get(url, headers=HEADERS)
    top_teams_data = response.json()

    extracted_players = parse_top_players(top_players_data)
    extracted_teams = parse_top_teams(top_teams_data)

    result = dict(
        players=extracted_players,
        teams=extracted_teams
    )

    return result

# ---------------------------- #

def extract_lineup_data(event_id: int, additional_data: dict) -> Dict[str, Any]:

    # additional data: {home: {id, name, namecode},away: {id, name, namecode}}

    url = f"{SOFASCORE_API}/event/{event_id}/lineups"
    response = rq.get(url, headers=HEADERS)
    data = response.json()

    if not data['confirmed']:
        return dict()

    else:
        # extracted data: {home: ..., away: ...}
        extracted = parse_lineup_data(data)

        extra_data = DotDict(additional_data)
        home_extra = extra_data.home
        away_extra = extra_data.away

        home_extra.manager = extract_manager_name(home_extra.id)
        away_extra.manager = extract_manager_name(away_extra.id)

        extracted['home'].update(dict(home_extra))
        extracted['away'].update(dict(away_extra))

        return extracted

# ---------------------------- #

def extract_result_data(event_id: int, additional_data: dict) -> Dict[str, Any]:
    
    # additional data: {home: {id, name, namecode},away: {id, name, namecode}}

    # process confirmed lineup firstly
    url = f"{SOFASCORE_API}/event/{event_id}/lineups"
    response = rq.get(url, headers=HEADERS)
    data = response.json()

    # extracted data: {home: ..., away: ...}
    lineup = parse_lineup_data(data, players_detailed=False)

    extra_data = DotDict(additional_data)
    home_extra = extra_data.home
    away_extra = extra_data.away

    best_worse_home = parse_player_statistics(lineup['home']['players'])
    best_worse_away = parse_player_statistics(lineup['away']['players'])

    # process statistics
    url = f"{SOFASCORE_API}/event/{event_id}/statistics"
    response = rq.get(url, headers=HEADERS)
    data = response.json()

    statistics = parse_event_statistics(data['statistics'])
    statistics['home'].update({**dict(home_extra), **best_worse_home})
    statistics['away'].update({**dict(away_extra), **best_worse_away})

    # get final score
    url = f"{SOFASCORE_API}/event/{event_id}"
    response = rq.get(url, headers=HEADERS)
    data = response.json()

    scores = parse_event_global_data(data)
    statistics['home'].update({'final_score' : scores['home']})
    statistics['away'].update({'final_score' : scores['away']})

    # add lineup scores
    sofascores = parse_player_scores(lineup['home']['players'] + lineup['away']['players'])
    statistics['sofascores'] = sofascores

    return statistics

# ---------------------------- #

def parse_event_global_data(data: dict) -> Dict[str, Any]:

    data = DotDict(data)
    event = data.event

    away_score = event.awayScore.display
    home_score = event.homeScore.display

    result = dict(
        home=home_score,
        away=away_score
    )

    return result

# ---------------------------- #

def extract_player_data(player_id: int) -> Dict[str, Any]:

    url = f"{SOFASCORE_API}/player/{player_id}"
    response = rq.get(url, headers=HEADERS)
    data = response.json()
    extracted = parse_player_data(data['player'])

    # national-team-statistics
    url = f"{SOFASCORE_API}/player/{player_id}/national-team-statistics"
    response = rq.get(url, headers=HEADERS)
    data = response.json()
    national_data = parse_player_data_national(data)

    extracted.update(national_data)

    return extracted

# ---------------------------- #

def parse_player_data_national(data: dict) -> Dict[str, Any]:
    
    if data['statistics']:
        stats = data['statistics'][0]

        goals = stats['goals']
        matches = stats['appearances']
    
    else:
        goals = 0
        matches = 0

    result = dict(
        national_team_goals=goals,
        national_team_matches=matches
    )

    return result

# ---------------------------- #

def extract_manager_name(team_id: int) -> Dict[str, Any]:
    
    url = f"{SOFASCORE_API}/team/{team_id}"
    response = rq.get(url, headers=HEADERS)
    data = response.json()

    data = DotDict(data)

    name = data.team.manager.name
    short_name = data.team.manager.shortName
    result = dict(name=name, short_name=short_name)

    return result

# ---------------------------- #

def parse_player_scores(players: List[Dict[str, Any]]) -> List[Tuple[int, float]]:

    result = [
        (x['player']['id'], x.get('statistics', dict()).get('rating', None))
        for x in players
    ]

    return result

# ---------------------------- #

def parse_player_statistics(players: List[Dict[str, Any]]) -> Dict[str, Any]:
    
    with_stats = list(filter(lambda x: x.get('statistics', dict()).get('rating', False), players))

    best_player = max(with_stats, key=lambda x: float(x['statistics']['rating']))
    worst_player = min(with_stats, key=lambda x: float(x['statistics']['rating']))

    best_player_name = best_player['player']['shortName'].upper()
    best_player_score = best_player['statistics']['rating']
    best_player_id = best_player['player']['id']

    worst_player_name = worst_player['player']['shortName'].upper()
    worst_player_score = worst_player['statistics']['rating']
    worst_player_id = worst_player['player']['id']

    result = dict(
        best_player_name=best_player_name,
        best_player_score=best_player_score,
        best_player_id=best_player_id,
        worst_player_name=worst_player_name,
        worst_player_score=worst_player_score,
        worst_player_id=worst_player_id
    )

    return result

# ---------------------------- #

def parse_event_statistics(statistics: dict) -> Dict[str, Any]:

    def _fetch_stat(stats: list, name: str) -> List[Dict[str, Any]]:
        return list(filter(lambda x: x['groupName'] == name, stats))[0]['statisticsItems']
    
    # ............................ #
    
    def _fetch_stat_item(stat: list, name: str) -> Dict[str, Any]:
        items = list(filter(lambda x: x['name'] == name, stat))
        
        if items:
            return items[0]
        
        else:
            return dict(
                name=name,
                home="0",
                away="0"
            )
    
    # ............................ #

    def _extract(stats: list) -> DotDict:
        possession = _fetch_stat(stats, 'Possession')
        shots = _fetch_stat(stats, 'Shots')
        shots_extra = _fetch_stat(stats, 'Shots extra')
        tvdata = _fetch_stat(stats, 'TVData')
        passes = _fetch_stat(stats, 'Passes')

        corner_kicks = DotDict(_fetch_stat_item(tvdata, 'Corner kicks'))
        ball_possession = DotDict(_fetch_stat_item(possession, 'Ball possession'))
        offsides = DotDict(_fetch_stat_item(tvdata, 'Offsides'))

        yellow_cards = DotDict(_fetch_stat_item(tvdata, 'Yellow cards'))
        red_cards = DotDict(_fetch_stat_item(tvdata, 'Red cards'))
        fouls = DotDict(_fetch_stat_item(tvdata, 'Fouls'))

        overall_passes = DotDict(_fetch_stat_item(passes, 'Passes'))
        successful_passes = DotDict(_fetch_stat_item(passes, 'Accurate passes'))

        goal_attempts = DotDict(_fetch_stat_item(shots_extra, 'Shots inside box'))
        total_shots = DotDict(_fetch_stat_item(shots, 'Total shots'))

        result = DotDict(
            corner_kicks=corner_kicks,
            ball_possession=ball_possession,
            offsides=offsides,
            yellow_cards=yellow_cards,
            red_cards=red_cards,
            overall_passes=overall_passes,
            successful_passes=successful_passes,
            goal_attempts=goal_attempts,
            total_shots=total_shots,
            fouls=fouls
        )

        return result

    # ............................ #
    
    def _process(stats: DotDict, team: str) -> Dict[str, Any]:
        
        corner_kicks = stats.corner_kicks[team]
        possession_percentage = stats.ball_possession[team]

        total_shots = stats.total_shots[team]
        goal_attempts = stats.goal_attempts[team]

        if int(total_shots) > 0:
            goal_attempts_percentage = f'{int(round(float(goal_attempts) / (float(total_shots)) * 100, 0))}%'
        
        else:
            goal_attempts_percentage = '0%'
        
        #! changing goal_attempts -> total_shots according to the requirement
        goal_attempts = total_shots
        
        offsides = stats.offsides[team]
        fouls = stats.fouls[team]
        yellow_cards = stats.yellow_cards[team]
        red_cards = stats.red_cards[team]
        overall_passes = stats.overall_passes[team]
        successful_passes = stats.successful_passes[team].split()[0]

        result =  dict(
            corner_kicks=corner_kicks,
            possession_percentage=possession_percentage,
            goal_attempts_percentage=goal_attempts_percentage,
            offsides=offsides,
            yellow_cards=yellow_cards,
            red_cards=red_cards,
            overall_passes=overall_passes,
            successful_passes=successful_passes,
            goal_attempts=goal_attempts,
            fouls=fouls
        )

        return result

    # ............................ #
    
    allstats = list(filter(lambda x: x['period'] == 'ALL', statistics))[0]
    allstats = allstats['groups']
    extracted_stats = _extract(allstats)

    home_stats = _process(extracted_stats, 'home')
    away_stats = _process(extracted_stats, 'away')

    result = dict(
        home=home_stats,
        away=away_stats
    )

    return result

# ---------------------------- #

def parse_event_data(event: dict) -> Dict[str, Any]:

    # dot access
    event = DotDict(event)
    
    event_id = event.id
    start_timestamp = event.startTimestamp

    # for some reason some round numbers missed
    round_num = -1 if event.get('roundInfo', None) is None else event.roundInfo.get('round', -1)

    event_status_code = event.status.code
    event_status_type = event.status.type
    hometeam_id = event.homeTeam.id
    hometeam_name = event.homeTeam.name
    hometeam_namecode = event.homeTeam.nameCode
    awayteam_id = event.awayTeam.id
    awayteam_name = event.awayTeam.name
    awayteam_namecode = event.awayTeam.nameCode

    record = dict(
        event_id=event_id,
        start_timestamp=start_timestamp,
        round_num=round_num,
        event_status_code=event_status_code,
        event_status_type=event_status_type,
        hometeam_id=hometeam_id,
        hometeam_name=hometeam_name,
        hometeam_namecode=hometeam_namecode,
        awayteam_id=awayteam_id,
        awayteam_name=awayteam_name,
        awayteam_namecode=awayteam_namecode
    )

    return record

# ---------------------------- #

def parse_player_data(player: dict) -> Dict[str, Any]:
    
    player = DotDict(player)

    shirt_number = player.shirtNumber
    player_id = player.id
    name = player.shortName
    position = player.position
    market_value = player.proposedMarketValue
    team_name = player.team.name

    result = dict(
        shirt_number=shirt_number,
        player_id=player_id,
        name=name,
        position=position,
        market_value=market_value,
        team_name=team_name
    )

    return result

# ---------------------------- #

def parse_lineup_data(lineup: dict, players_detailed: bool = True) -> Dict[str, Any]:

    def _extract(data: DotDict, players_detailed: bool) -> Dict[str, Any]:
        formation = data.formation

        if players_detailed:
            players = list(map(lambda x: DotDict(x), data.players))
            players = list(filter(lambda x: not x.substitute, players))
            players = list(map(lambda x: x.player.id, players))
            players = list(map(lambda x: extract_player_data(x), players))
        
        else:
            players = data.players

        result = dict(formation=formation, players=players)

        return result
    
    # ............................ #
        
    lineup = DotDict(lineup)

    home_data = lineup.home
    away_data = lineup.away

    home_extracted = _extract(home_data, players_detailed)
    away_extracted = _extract(away_data, players_detailed)

    result = dict(home=home_extracted, away=away_extracted)

    return result

# ---------------------------- #

def parse_top_players(top_players: dict) -> Dict[str, Any]:

    def _extract(players: dict, stat: str, fix_stat: str = None, top_number: int = 1) -> Tuple[str, Any]:

        by_stat = players[stat]

        name = by_stat[top_number - 1]['player']['name'].upper()
        id_ = by_stat[top_number - 1]['player']['id']
        numb = by_stat[top_number - 1]['statistics'][fix_stat or stat]

        return dict(player_name=name, number=numb, id=id_)
    
    # ............................ #

    top = top_players['topPlayers']

    most_goals = _extract(top, 'goals')
    most_assists = _extract(top, 'assists')
    most_goals_and_assists_combined = _extract(top, 'goalsAssistsSum')
    highest_pass_accuracy = _extract(top, 'accuratePasses', 'accuratePassesPercentage')
    highest_pass_accuracy['number'] = f"{round(highest_pass_accuracy['number'], 0):.0f}%"

    most_yellow_cards = _extract(top, 'yellowCards')
    most_red_cards = _extract(top, 'redCards')
    most_tackles = _extract(top, 'tackles')

    result = dict(
        most_goals=most_goals,
        most_assists=most_assists,
        most_goals_and_assists_combined=most_goals_and_assists_combined,
        highest_pass_accuracy=highest_pass_accuracy,
        most_yellow_cards=most_yellow_cards,
        most_red_cards=most_red_cards,
        most_tackles=most_tackles
    )

    return result

# ---------------------------- #

def parse_top_teams(top_teams: dict) -> Dict[str, Any]:
    
    def _extract(teams: dict, stat: str, fix_stat: str = None, top_number: int = 1) -> Tuple[str, Any]:

        by_stat = teams[stat]

        name = by_stat[top_number - 1]['team']['name']
        id_ = by_stat[top_number - 1]['team']['id']
        numb = by_stat[top_number - 1]['statistics'][fix_stat or stat]

        return dict(team_name=name, number=numb, id=id_)
    
    # ............................ #

    top = top_teams['topTeams']

    most_goals_scored = _extract(top, 'goalsScored')
    most_goals_against = _extract(top, 'goalsConceded', top_number=0) # 0 -> -1 -> last element instead of first
    least_goals_against = _extract(top, 'goalsConceded')

    result = dict(
        most_goals_scored=most_goals_scored,
        most_goals_against=most_goals_against,
        least_goals_against=least_goals_against
    )

    return result

# ---------------------------- #

def rewrap_key_player(x: dict) -> dict:

    return dict(
        name=x['name'].upper(), 
        number_country_games=x['national_team_matches'], 
        club=x['team_name'], 
        market_value=x['market_value'],
        goals=x['national_team_goals'],
        id=x['player_id']
    )
