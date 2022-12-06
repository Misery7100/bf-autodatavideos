import os
import sqlalchemy as sa

from datetime import datetime
from sqlalchemy.orm import Session

from core.db import build_connection_url
from database.tables import *

from core.sofascore import extract_tournament_biweekly_data
from core.plainly import prepare_tournament_request, make_render_request

# ---------------------------- #

def send_tournament_biweekly_directly(

        dbengine: sa.engine.Engine,
        auth_key: str
        
    ) -> None:
        
        now = datetime.now()
        strdate = now.strftime('%d-%m-%Y')

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
                                project_id="1358e03e-16da-4c2e-9647-cf17af82b38f",
                                template_id="836d0943-d47d-47f9-a430-5923153abc22",
                                auth_key=auth_key
                            )
                
                print(response.json())

                session.add(TournamentScheduleHistory(date_scheduled=strdate))
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

    PLAINLY_AUTH_KEY = os.environ.get('PLAINLY_AUTH_KEY')

    dburl = build_connection_url(**dbcreds)

    # check all tables exist
    engine = sa.create_engine(
                dburl,
                pool_recycle=30,
                connect_args={'options': '-csearch_path=common'}
            )

    send_tournament_biweekly_directly(engine, PLAINLY_AUTH_KEY)

    return {
        'statusCode': 200,
        'body': None,
        'headers': {
            "Content-Type": "application/json"
        }
    }