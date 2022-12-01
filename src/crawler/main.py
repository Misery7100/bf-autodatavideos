import os
import sqlalchemy as sa
import threading
import time

from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import update
from sqlalchemy.dialects.postgresql import insert

from database.tables import *
from core.common import read_yaml
from core.db import build_connection_url
from core.messaging import connect_to_queue, send_message
from core.sofascore import extract_all_events_tournament, extract_tournament_biweekly_data
from core.plainly import prepare_tournament_request, make_render_request

# ---------------------------- #

def get_event_updates(
        
        dbengine: sa.engine.Engine, 
        period: int = 300
    
    ):

    while True:

        # tournament and season hardcoded for a while
        new_events = extract_all_events_tournament(tournament_id=41087, season=16)
        extracted_event_ids = set(map(lambda x: x['event_id'], new_events))

        with Session(dbengine) as session:

            exist_event_ids = session.query(EventsGlobal.event_id).all()
            exist_event_ids = set(map(lambda x: x._data[0], exist_event_ids))

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

        time.sleep(period)

# ---------------------------- #

def schedule_result_calls(

        dbengine: sa.engine.Engine,
        queue: object,
        period: int = 30
        
    ) -> None:

    while True:
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
            
            session.close()
        
        time.sleep(period)

# ---------------------------- #

def schedule_result_lineup_calls(

        dbengine: sa.engine.Engine,
        queue: object,
        period: int = 30,
        soon_thresh_mins: int = 15

    ) -> None:

    soon_thresh_secs = soon_thresh_mins * 60

    while True:
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
        
        time.sleep(period)

# ---------------------------- #

def schedule_lineup_calls(

        dbengine: sa.engine.Engine,
        queue: object,
        period: int = 30,
        soon_thresh_mins: int = 15
        
    ) -> None:

    soon_thresh_secs = soon_thresh_mins * 60

    while True:
        now_timestamp = datetime.now().timestamp()

        with Session(dbengine) as session:

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
        
        time.sleep(period)

# ---------------------------- #

def send_tournament_biweekly_directly(

        dbengine: sa.engine.Engine,
        period: int = 60
        
    ) -> None:

    while True:
        
        now = datetime.now()
        weekday = now.weekday()
        hour = now.time().hour
        minute = now.time().minute
        strdate = now.strftime('%d-%m-%Y')

        if weekday in [2, 6] and hour == 9 and 0 < minute < 10:

            with Session(dbengine) as session:
                scheduled = (session
                                .query(TournamentScheduleHistory)
                                .where(TournamentScheduleHistory.date_scheduled == strdate)
                                .one_or_none()
                            )
                
                if scheduled is None:

                    extracted = extract_tournament_biweekly_data(tournament_id=41087, season=16)
                    parameters_tournament = prepare_tournament_request(extracted, dbengine)
                    response = make_render_request(
                                    parameters=parameters_tournament,
                                    project_id="781c273c-8e12-4aff-b844-ab7f59284b60",
                                    template_id="21e5ad1b-dccb-44aa-a78f-0869d1cf60a9",
                                    auth_key=os.environ.get('PLAINLY_AUTH_KEY')
                                )
                    
                    print(response.json())

                    session.add(TournamentScheduleHistory(date_scheduled=strdate))
                    session.commit()

                session.close()
        
        time.sleep(period)

# ---------------------------- #

def repeat_calls(

        dbengine: sa.engine.Engine,
        queue: object,
        period: int = 30
        
    ) -> None:

    while True:
        now_timestamp = datetime.now().timestamp()
        
        with Session(dbengine) as session:

            broken_lineups = (session
                            .query(EventsGlobal.event_id, EventLineups.event_id)
                            .join(EventLineups)
                            .where(
                                (EventLineups.call_scheduled == True) & \
                                (EventLineups.plainly_success == False)
                            )
                            .all()
                        )
            
            broken_results = (session
                            .query(EventsGlobal.event_id, EventResults.event_id)
                            .join(EventResults)
                            .where(
                                (EventResults.call_scheduled == True) & \
                                (EventResults.plainly_success == False)
                            )
                            .all()
                        )

            broken_lineups_ids = list(map(lambda x: x._data[0], broken_lineups))
            broken_results_ids = list(map(lambda x: x._data[0], broken_results))

            if broken_lineups_ids:

                for event_id in broken_lineups_ids:
                    send_message(queue, body='lineup-event', event_id=event_id, processing_type='lineup')
                
                stmt = (
                        update(EventLineups)
                        .where(EventLineups.event_id.in_(broken_lineups_ids))
                        .values(call_scheduled=True, scheduled_timestamp=now_timestamp)
                    )
                session.execute(stmt)
                session.commit()
            
            if broken_results_ids:

                for event_id in broken_results_ids:
                    send_message(queue, body='result-event', event_id=event_id, processing_type='result')
                
                stmt = (
                        update(EventResults)
                        .where(EventResults.event_id.in_(broken_results_ids))
                        .values(call_scheduled=True, scheduled_timestamp=now_timestamp)
                    )
                session.execute(stmt)
                session.commit()
            
            session.close()
        
        time.sleep(period)

# ---------------------------- #

def main():

    config = read_yaml('config.yml')

    # rds connection
    dbcreds = read_yaml('secrets/databases.yml').default
    dburl = build_connection_url(**dbcreds)

    # check all tables exist 
    engine = sa.create_engine(
                dburl,
                future=True,
                connect_args={'options': '-csearch_path=common,public'}
            )
    Base.metadata.create_all(engine, Base.metadata.tables.values(), checkfirst=True)
    queue = connect_to_queue(config.queue.region, config.queue.queue_name)

    # run objectives as threads
    get_updates_thread = threading.Thread(
            target=lambda: get_event_updates(
                dbengine=engine, 
                period=config.timeout.get_updates
            ), 
            daemon=True
        )

    # schedule_result_calls_thread = threading.Thread(
    #         target=lambda: schedule_result_calls(
    #             dbengine=engine, 
    #             period=config.timeout.schedule_calls,
    #             queue=queue
    #         ),
    #         daemon=True
    #     )
    
    # schedule_lineup_calls_thread = threading.Thread(
    #         target=lambda: schedule_lineup_calls(
    #             dbengine=engine, 
    #             period=config.timeout.schedule_calls,
    #             queue=queue
    #         ),
    #         daemon=True
    #     )

    schedule_result_lineup_calls_thread = threading.Thread(
        target=lambda: schedule_lineup_calls(
            dbengine=engine, 
            period=config.timeout.schedule_calls,
            queue=queue
        ),
        daemon=True
    )
    
    # repeat_calls_thread = threading.Thread(
    #         target=lambda: repeat_calls(
    #             dbengine=engine, 
    #             period=config.timeout.repeat_calls,
    #             queue=queue
    #         ),
    #         daemon=True
    #     )
    
    send_tournament_biweekly_directly_thread = threading.Thread(
            target=lambda: send_tournament_biweekly_directly(
                dbengine=engine
            ),
            daemon=True
        )

    get_updates_thread.start()
    schedule_result_lineup_calls_thread.start()
    send_tournament_biweekly_directly_thread.start()

    # necessary for infinite evaluation
    while True:
        pass

# ---------------------------- #

if __name__ == '__main__':
    main()