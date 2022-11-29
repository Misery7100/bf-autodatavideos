import os
import sqlalchemy as sa

from datetime import datetime
from sqlalchemy.orm import Session

from core.db import build_connection_url
from core.messaging import connect_to_queue, send_message
from core.plainly import *
from core.sofascore import extract_lineup_data, extract_result_data
from database.tables import *

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

# ---------------------------- #

def lambda_handler(event, context):

    dbcreds = {
        'db'        : os.environ.get('RDS_DATABASE'),
        'user'      : os.environ.get('RDS_USER'),
        'password'  : os.environ.get('RDS_PASSWORD'),
        'host'      : os.environ.get('RDS_HOST'),
    }

    PLAINLY_AUTH_KEY = os.environ.get('PLAINLY_AUTH_KEY')

    dburl = build_connection_url(**dbcreds)

    # check all tables exist
    engine = sa.create_engine(
                dburl,
                pool_recycle=30,
                connect_args={'options': '-csearch_path=common', 'connect_timeout': 45}
            )

    messages = event.get('Records')
    num_messages = len(messages)
    now_timestamp = datetime.now().timestamp()
    errors = 0

    for msg in messages:

        attributes = msg['messageAttributes']
        event_id = int(attributes['event_id']['stringValue'])
        processing_type = attributes['processing_type']['stringValue']

        if processing_type == 'lineup':

            with Session(engine) as session:
                data = session.query(EventsGlobal).get(event_id)
            
                if not data is None:
                    additional_data = dict(
                        home=dict(
                            id=data.hometeam_id,
                            name=data.hometeam_name.upper(),
                            namecode=data.hometeam_namecode.upper()
                        ),
                        away=dict(
                            id=data.awayteam_id,
                            name=data.awayteam_name.upper(),
                            namecode=data.awayteam_namecode.upper()
                        )
                    )
                    lineup_extracted = extract_lineup_data(
                        event_id=event_id, 
                        additional_data=additional_data
                    )

                    if lineup_extracted:

                        home_players = lineup_extracted['home']['players']
                        away_players = lineup_extracted['away']['players']
                        home_plids = list(map(lambda x: x['player_id'], home_players))
                        away_plids = list(map(lambda x: x['player_id'], away_players))

                        home_scores = (session
                                        .query(
                                            EventResultsPlayerHistory.player_id,
                                            sa.sql.func.avg(EventResultsPlayerHistory.sofascore).label('average')
                                        )
                                        .where(
                                            (EventResultsPlayerHistory.player_id.in_(home_plids)) & \
                                            (EventResultsPlayerHistory.sofascore != None)
                                        )
                                        .group_by(EventResultsPlayerHistory.player_id)
                                        .order_by(sa.desc('average'))
                                        .limit(3)
                                        .all()
                                    )
                        
                        away_scores = (session
                                        .query(
                                            EventResultsPlayerHistory.player_id,
                                            sa.sql.func.avg(EventResultsPlayerHistory.sofascore).label('average')
                                        )
                                        .where(
                                            (EventResultsPlayerHistory.player_id.in_(away_plids)) & \
                                            (EventResultsPlayerHistory.sofascore != None)
                                        )
                                        .group_by(EventResultsPlayerHistory.player_id)
                                        .order_by(sa.desc('average'))
                                        .limit(3)
                                        .all()
                                    )
                        
                        home_key_players_id = list(map(lambda x: x[0], home_scores))
                        away_key_players_id = list(map(lambda x: x[0], away_scores))

                        home_3_key_players = list(sorted(
                            filter(lambda x: x['player_id'] in home_key_players_id, home_players), 
                            key=lambda x: home_key_players_id.index(x['player_id'])))
                        away_3_key_players = list(sorted(
                            filter(lambda x: x['player_id'] in away_key_players_id, away_players), 
                            key=lambda x: away_key_players_id.index(x['player_id'])))

                        home_3_key_players = list(map(rewrap_key_player, home_3_key_players))
                        away_3_key_players = list(map(rewrap_key_player, away_3_key_players))

                        plainly_reqs = prepare_lineup_request(lineup_extracted, home_3_key_players, away_3_key_players)
                        print(plainly_reqs)
                        # call plainly API
                        # ----

                        data = session.query(EventLineups).get(event_id)
                        data.plainly_success = True
                        session.commit()
                        session.close()
                    
                    else:

                        print('LINEUP NOT CONFIRMED')  

                        # TODO: add config (better to have a common configuration file)
                        queue = connect_to_queue(region='eu-central-1', queue_name='bf-autodatavideos-mi')
                        send_message(queue, body='lineup-event', event_id=event_id, processing_type='lineup', delay=60)

                    # repush message via boto

        elif processing_type == 'result':

            with Session(engine) as session:
                data = session.query(EventsGlobal).get(event_id)

                if not data is None:
                    additional_data = dict(
                        home=dict(
                            id=data.hometeam_id,
                            name=data.hometeam_name.upper(),
                            namecode=data.hometeam_namecode.upper()
                        ),
                        away=dict(
                            id=data.awayteam_id,
                            name=data.awayteam_name.upper(),
                            namecode=data.awayteam_namecode.upper()
                        )
                    )

                    result_extracted = extract_result_data(
                        event_id=event_id, 
                        additional_data=additional_data
                    ) 

                    result_parameters = prepare_result_request(result_extracted, engine)

                    # call plainly API
                    # roghly estimate end_timestamp with 130 minutes game and check for threshold 
                    # within 30 minutes
                    seconds_after_end = now_timestamp - (data.start_timestamp + 130 * 60)

                    if seconds_after_end < 30 * 60:
                        
                        plainly_response = make_render_request(
                            parameters=result_parameters,
                            project_id="ee888f8c-ac76-4785-919f-afa91df19b43",
                            template_id="d8b6cf18-45fa-4c18-b83a-4b2d8a45df1e",
                            auth_key=PLAINLY_AUTH_KEY
                        )

                        print(plainly_response)
                    
                    else:
                        print(f'Too old event: {seconds_after_end=}')

                    # push player scores for the event
                    sofascores = result_extracted['sofascores']

                    data = session.query(EventResults).get(event_id)
                    data.plainly_success = True
                    session.commit()

                    event_ = session.query(EventsGlobal).get(event_id)
                    records = [
                                EventResultsPlayerHistory(
                                    event=event_, 
                                    player_id=x[0], 
                                    sofascore=x[1]
                                )
                                for x in sofascores
                            ]
                    session.add_all(records)
                    session.commit()
                    session.close()
        
        else:
            errors += 1
    
    return {
        'statusCode': 200 if errors == 0 else 400,
        'body': {
            'num_messages' : num_messages,
            'num_errors'   : errors
        },
        'headers': {
            "Content-Type": "application/json"
        }
    }