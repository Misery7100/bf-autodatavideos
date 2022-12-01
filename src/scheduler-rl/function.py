import os
import sqlalchemy as sa

from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import update

from core.common import read_yaml
from core.db import build_connection_url
from core.messaging import connect_to_queue, send_message
from database.tables import *

# ---------------------------- #

def schedule_result_lineup_calls(

        dbengine: sa.engine.Engine,
        queue: object,
        soon_thresh_mins: int = 15

    ) -> None:

    soon_thresh_secs = soon_thresh_mins * 60
    now_timestamp = datetime.now().timestamp()

    with Session(dbengine) as session:

        ended_events = (session.query(EventsGlobal.event_id, EventResults.event_id)
                                .join(EventResults)
                                .where(
                                    (EventResults.call_scheduled == False) & \
                                    (EventsGlobal.event_status_code == 100)
                                )
                                .all()
                            )
                
        ended_event_ids = list(map(lambda x: x._data[0], ended_events))

        if ended_event_ids:

            for event_id in ended_event_ids:
                send_message(queue, body='result-event', event_id=event_id, processing_type='result')
            
            stmt = (
                    update(EventResults)
                    .where(EventResults.event_id.in_(ended_event_ids))
                    .values(call_scheduled=True, scheduled_timestamp=now_timestamp)
                )
            session.execute(stmt)
            session.commit()
        
        soon_events = (session
                        .query(EventsGlobal.event_id, EventLineups.event_id)
                        .join(EventLineups)
                        .where(
                            (EventLineups.call_scheduled == False) & \
                            (EventsGlobal.start_timestamp - now_timestamp > 0) & \
                            (EventsGlobal.start_timestamp - now_timestamp < soon_thresh_secs)
                        )
                        .all()
                    )
        
        soon_event_ids = list(map(lambda x: x._data[0], soon_events))

        if soon_event_ids:

            for event_id in soon_event_ids:
                send_message(queue, body='lineup-event', event_id=event_id, processing_type='lineup')
            
            stmt = (
                    update(EventLineups)
                    .where(EventLineups.event_id.in_(soon_event_ids))
                    .values(call_scheduled=True, scheduled_timestamp=now_timestamp)
                )
            session.execute(stmt)
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
    config = read_yaml('config.yml')

    # check all tables exist
    engine = sa.create_engine(
                dburl,
                pool_recycle=30,
                connect_args={'options': '-csearch_path=common'}
            )
    queue = connect_to_queue(config.queue.region, config.queue.queue_name)

    schedule_result_lineup_calls(engine, queue)

    return {
        'statusCode': 200,
        'body': None,
        'headers': {
            "Content-Type": "application/json"
        }
    }