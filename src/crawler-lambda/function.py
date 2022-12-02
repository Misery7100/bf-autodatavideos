import os
import sqlalchemy as sa

from sqlalchemy.orm import Session
from sqlalchemy.dialects.postgresql import insert

from core.db import build_connection_url
from core.plainly import *
from core.sofascore import extract_all_events_tournament
from database.tables import *

# ---------------------------- #

def get_event_updates(
        
        dbengine: sa.engine.Engine
   
    ):

    # tournament and season hardcoded for a while
    new_events = extract_all_events_tournament(tournament_id=41087, season=16)
    extracted_event_ids = set(map(lambda x: x['event_id'], new_events))

    print(f'{extracted_event_ids=}')

    with Session(dbengine) as session:

        exist_event_ids = session.query(EventsGlobal.event_id).all()
        exist_event_ids = set(map(lambda x: x._data[0], exist_event_ids))

        print(f'{exist_event_ids=}')

        new_event_ids = list(extracted_event_ids.difference(exist_event_ids))

        stmt = insert(EventsGlobal).values(new_events)
        stmt = stmt.on_conflict_do_update(
            index_elements=[EventsGlobal.event_id],
            set_=dict(
                start_timestamp=stmt.excluded.start_timestamp,
                event_status_code=stmt.excluded.event_status_code,
                event_status_type=stmt.excluded.event_status_type
            )
        )
        session.execute(stmt)

        if new_event_ids:
            lineups = [
                EventLineups(event=session.query(EventsGlobal).get(id_)) 
                for id_ in new_event_ids
            ]
            session.add_all(lineups)
            results = [
                EventResults(event=session.query(EventsGlobal).get(id_)) 
                for id_ in new_event_ids
            ]
            session.add_all(results)

        session.commit()
        session.close()

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
    engine = sa.create_engine(
                dburl,
                pool_recycle=30,
                echo=True,
                echo_pool=True,
                connect_args={'options': '-csearch_path=common'}
            )
    
    Base.metadata.create_all(engine, Base.metadata.tables.values(), checkfirst=True)
    get_event_updates(engine)

    return {
        'statusCode': 200,
        'body': None,
        'headers': {
            "Content-Type": "application/json"
        }
    }