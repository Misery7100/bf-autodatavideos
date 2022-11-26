import os
import sqlalchemy as sa

from sqlalchemy.orm import Session
from sqlalchemy.pool import NullPool

from core.db import build_connection_url
from core.messaging import connect_to_queue, send_message
from core.sofascore import extract_lineup_data, extract_result_data
from database.tables import *

# ---------------------------- #

def lambda_handler(event, context):

    print('^-----^ Event info ^-----^')
    print(event)
    print('vvvvvvvvvvvvvvvvvvvvvvvvvv')

    dbcreds = {
        'db'        : os.environ.get('RDS_DATABASE'),
        'user'      : os.environ.get('RDS_USER'),
        'password'  : os.environ.get('RDS_PASSWORD'),
        'host'      : os.environ.get('RDS_HOST'),
    }

    dburl = build_connection_url(**dbcreds)

    # check all tables exist
    engine = sa.create_engine(
                dburl, 
                echo=True,
                echo_pool=True, 
                future=True,
                connect_args={'options': '-csearch_path=common'}
            )
    Base.metadata.create_all(engine, Base.metadata.tables.values(), checkfirst=True)

    messages = event.get('Records')
    num_messages = len(messages)
    errors = 0

    for msg in messages:

        attributes = msg['messageAttributes']
        event_id = int(attributes['event_id']['stringValue'])
        processing_type = attributes['processing_type']['stringValue']

        if processing_type == 'lineup':

            with Session(engine) as session:
                data = session.query(EventsGlobal).where(EventsGlobal.event_id == event_id).one_or_none()
                session.close()
            
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
                    print(lineup_extracted)

                    # call plainly API
                    # ----
                
                else:  

                    # TODO: add config (better to have a common configuration file)
                    queue = connect_to_queue(region='eu-central-1', queue_name='bf-autodatavideos-mi')
                    send_message(queue, body='lineup-event', event_id=event_id, processing_type='lineup', delay=60)

                    # repush message via boto

        elif processing_type == 'result':

            with Session(engine) as session:
                data = session.query(EventsGlobal).where(EventsGlobal.event_id == event_id).one_or_none()
                session.close()

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

                # call plainly API

                print(result_extracted)

                # push player scores for the event
                sofascores = result_extracted['sofascores']
                
                with Session(engine) as session:
                    event = session.query(EventsGlobal).get(event_id)
                    records = [
                                EventResultsPlayerHistory(
                                    event=event, 
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
    
    engine.dispose()
    
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