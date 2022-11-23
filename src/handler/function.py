import os
import sqlalchemy as sa

from sqlalchemy.orm import Session

from core.db import build_connection_url
from core.sofascore import extract_lineup_data, extract_result_data
from database.tables import *

# ---------------------------- #

def lambda_handler(event, context):

    dbcreds = {
        'db'        : os.environ.get('RDS_DATABASE'),
        'user'      : os.environ.get('RDS_USER'),
        'password'  : os.environ.get('RDS_PASSWORD'),
        'host'      : os.environ.get('RDS_HOST'),
    }

    dburl = build_connection_url(**dbcreds)

    # check all tables exist
    engine = sa.create_engine(dburl, echo=True, future=True, connect_args={'options': '-csearch_path=common'})
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

                # call plainly

                print(lineup_extracted)

        elif processing_type == 'result':

            with Session(engine) as session:
                data = session.query(EventsGlobal).where(EventsGlobal.event_id == event_id).one_or_none()

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

                # call plainly

                print(result_extracted)
        
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