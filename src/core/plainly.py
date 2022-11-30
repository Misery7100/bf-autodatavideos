import n2w
import requests
import sqlalchemy as sa

from copy import deepcopy
from requests.auth import HTTPBasicAuth
from sqlalchemy.orm import Session

from core.common import flatten
from database.tables import *
from datetime import datetime

# ---------------------------- #

placeholder_player_img = 'http://twc-rss.com/autovideos/data/wm/Spielerportrait/no_player_image.png'

# ---------------------------- #

def prepare_lineup_request(

        lineup_extracted: dict, 
        home_keyplayers: list,
        away_keyplayers: list
    
    ) -> dict:

    def _rewrap(lineup: dict, keyplayers: list) -> dict:
        
        screen_one = dict(
            country=lineup['name'].upper(),
            formation=lineup['formation'],
            trainer_name=lineup['manager']['short_name'].upper()
        )

        for i, player in enumerate(lineup['players']):

            key = 'player_goal_keeper' if i == 0 else f'player_{n2w.convert(i)}'
            
            screen_one[key] = dict(
                                name=player['name'].upper(),
                                number=player['shirt_number']
                            )
        
        screen_two = dict(
            key_player_one=keyplayers[0]
        )
        screen_three = dict(
            key_player_two=keyplayers[1]
        )
        screen_four = dict(
            key_player_three=keyplayers[2]
        )

        result = dict(
            screen_one=screen_one,
            screen_two=screen_two,
            screen_three=screen_three,
            screen_four=screen_four
        )

        return result

    home = lineup_extracted['home']
    away = lineup_extracted['away']

    home_request = _rewrap(home, home_keyplayers)
    away_request = _rewrap(away, away_keyplayers)

    result = flatten(dict(home=home_request, away=away_request))

    return result

# ---------------------------- #

def prepare_result_request(
    
        result_extracted: dict,
        dbengine: sa.engine.Engine
    
    ) -> dict:

    def _get_stat(stat: str, home: dict, away: dict, astype = None) -> dict:

        if astype is None:
            result = dict(
                home=home[stat],
                away=away[stat]
            )
        
        else:
            result = dict(
                home=astype(home[stat]),
                away=astype(away[stat])
            )
        
        return result
    
    # ............................ #

    def _get_best_worst(mode: str, home: dict, away: dict):
        
        mode_names = (home[f'{mode}_player_name'], away[f'{mode}_player_name'])
        mode_ids = (home[f'{mode}_player_id'], away[f'{mode}_player_id'])
        mode_scores = (home[f'{mode}_player_score'], away[f'{mode}_player_score'])

        if mode == 'best':
            idx = mode_scores.index(max(mode_scores))
        
        else:
            idx = mode_scores.index(min(mode_scores))

        return dict(
            name=mode_names[idx],
            score=f'{mode_scores[idx]:.1f}',
            id=mode_ids[idx]
        )

    # ............................ #

    def _replace_player_from_db(ori: dict, db: object) -> dict:

        orig = deepcopy(ori)

        if db is None:
            orig['image_url'] = placeholder_player_img

        else:
            orig['name'] = db.name_ger.strip().upper()
            orig['image_url'] = db.picture_url

        orig.pop('id')

        return orig

    # ............................ #

    home = result_extracted['home']
    away = result_extracted['away']

    with Session(dbengine) as session:
        country_home = session.query(TeamDetails).get(home['id'])
        country_away = session.query(TeamDetails).get(away['id'])
        country_home_image_url = country_home.picture_url
        country_away_image_url = country_away.picture_url
        country_home_name = country_home.name_ger.strip().upper()
        country_away_name = country_away.name_ger.strip().upper()

    screen_one = dict(
        names=dict(home=country_home_name, away=country_away_name),
        final_score=_get_stat('final_score', home, away, str),
        goal_attempts=_get_stat('goal_attempts', home, away),
        fouls=_get_stat('fouls', home, away),
        corner_kicks=_get_stat('corner_kicks', home, away),
        offsides=_get_stat('offsides', home, away),
        yellow_cards=_get_stat('yellow_cards', home, away),
        red_cards=_get_stat('red_cards', home, away),
        passes=_get_stat('overall_passes', home, away),
        pass_success=_get_stat('successful_passes', home, away),
        perc_ball_possession=_get_stat('possession_percentage', home, away),
        goal_attempts_percentage=_get_stat('goal_attempts_percentage', home, away),
        country_home_image_url=country_home_image_url,
        country_away_image_url=country_away_image_url
    )

    best_player = _get_best_worst('best', home, away)
    worst_player = _get_best_worst('worst', home, away)

    with Session(dbengine) as session:
        best_player_db = session.query(PlayerDetails).get(best_player['id'])
        worst_player_db = session.query(PlayerDetails).get(worst_player['id'])

    best_player = _replace_player_from_db(best_player, best_player_db)
    worst_player = _replace_player_from_db(worst_player, worst_player_db)

    screen_two = dict(
        best_player=best_player
    )
    screen_three = dict(
        worst_player=worst_player
    )

    result = flatten(dict(
        screen_one=screen_one,
        screen_two=screen_two,
        screen_three=screen_three
    ))

    return result

# ---------------------------- #

def prepare_tournament_request(
    
        result_extracted: dict,
        dbengine: sa.engine.Engine
    
    ) -> dict:

    def _replace_player_from_db(ori: dict, db: object) -> dict:

        orig = deepcopy(ori)

        if db is None:
            orig['player_image'] = placeholder_player_img

        else:
            orig['player_name'] = db.name_ger.strip().upper()
            orig['player_image'] = db.picture_url

        orig['number'] = str(orig['number'])
        orig.pop('id')

        return orig
    
    # ............................ #

    def _replace_team_from_db(ori: dict, db: object) -> dict:

        print(ori)

        orig = deepcopy(ori)
        orig['team_name'] = db.name_ger.strip().upper()
        orig['team_image'] = db.picture_url
        orig['number'] = str(orig['number'])
        orig.pop('id')

        return orig

    # ............................ #

    teams = result_extracted['teams']
    players = result_extracted['players']

    with Session(dbengine) as session:

        for param, team_details in teams.items():
            team_ = session.query(TeamDetails).get(team_details['id'])
            teams[param] = _replace_team_from_db(team_details, team_)
        
        for param, player_details in players.items():
            player_ = session.query(PlayerDetails).get(player_details['id'])
            players[param] = _replace_player_from_db(player_details, player_)

    teams = flatten(teams)
    players = flatten(players)

    # hardcoded for a while
    week_number = (datetime.now() - datetime.strptime('2022-11-20', '%Y-%m-%d')).days // 7 + 1

    result = {**teams, **players, 'week_number' : week_number}

    return result

# ---------------------------- #

def make_render_request(
        
        parameters: dict, 
        project_id: str, 
        template_id: str,
        auth_key: str
    
    ):

    url = 'https://api.plainlyvideos.com/api/v2/renders'

    headers = {
        "Content-Type" : "application/json"
    }

    auth = HTTPBasicAuth(auth_key, "")

    data = {
        "projectId"     : project_id,
        "templateId"    : template_id,
        "parameters"    : parameters,
        "outputFormat"  : {"format" :"MP4"}
    }

    response = requests.post(
                    url, 
                    headers=headers, 
                    json=data, 
                    auth=auth
                )
    
    return response