import n2w

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

    result = dict(home=home_request, away=away_request)

    return result

# ---------------------------- #

def prepare_result_request(result_extracted: dict) -> dict:

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
        mode_scores = (home[f'{mode}_player_score'], away[f'{mode}_player_score'])

        if mode == 'best':
            idx = mode_scores.index(max(mode_scores))
        
        else:
            idx = mode_scores.index(min(mode_scores))

        return dict(
            name=mode_names[idx],
            score=str(mode_scores[idx])
        )

    # ............................ #

    home = result_extracted['home']
    away = result_extracted['away']

    screen_one = dict(
        names=_get_stat('name', home, away),
        final_score=_get_stat('final_score', home, away, str),
        goal_attempts=_get_stat('goal_attempts', home, away),
        fouls=_get_stat('fouls', home, away),
        corner_kicks=_get_stat('corner_kicks', home, away),
        offsides=_get_stat('offsides', home, away),
        yellow_cards=_get_stat('yellow_cards', home, away),
        red_cards=_get_stat('red_cards', home, away),
        passes=_get_stat('overall_passes', home, away),
        pass_success=_get_stat('successful_passes', home, away),
        perc_ball_possession=_get_stat('possession_percentage', home, away)
    )

    screen_two = dict(
        best_player=_get_best_worst('best', home, away)
    )
    screen_three = dict(
        worst_player=_get_best_worst('worst', home, away)
    )

    result = dict(
        screen_one=screen_one,
        screen_two=screen_two,
        screen_three=screen_three
    )

    return result

# ---------------------------- #
