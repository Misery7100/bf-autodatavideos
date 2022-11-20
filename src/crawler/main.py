import boto3
import sqlalchemy as sa
import time

from sqlalchemy.orm import Session

from ladles.sofascore import extract_all_events_tournament
from ladles.db import Base, EventsGlobal
from utils.common import read_yaml
from utils.db import build_connection_url

# ---------------------------- #

def main():

    config = read_yaml('config.yml')

    # rds connection
    dbcreds = read_yaml('secrets/databases.yml').default
    dburl = build_connection_url(**dbcreds)

    engine = sa.create_engine(dburl, echo=True, future=True, connect_args={'options': '-csearch_path=common,public'})
    Base.metadata.create_all(engine, Base.metadata.tables.values(), checkfirst=True)

    # single check
    # new_events = extract_all_events_tournament(tournament_id=41087, season=16)

    # with Session(engine) as session:
    #     records = [EventsGlobal(**event) for event in new_events]
    #     session.add_all(records)
    #     session.commit()

    # boto check
    sqs = boto3.resource('sqs', region_name='eu-central-1')
    queue = sqs.get_queue_by_name(QueueName='bf-autodatavideos-mi')

    for i in range(30):
        queue.send_message(MessageBody="line-up-event", MessageAttributes={
            "event_id" : {
                "DataType" : "Number",
                "StringValue" : "10230541"
            },
            "processing_type" : {
                "DataType" : "String",
                "StringValue" : "line-up"
            },
            "number_artificial" : {
                "DataType" : "Number",
                "StringValue" : str(i + 1)
            }
        })
        time.sleep(1)

    # while True:
    #     new_events = extract_all_events_tournament(tournament_id=41087, season=16)

    #     with Session(engine) as session:
    #         records = [EventsGlobal(**event) for event in new_events]
    #         session.add_all(records)
    #         session.commit()

    #     time.sleep(config.timeout)

if __name__ == '__main__':
    main()