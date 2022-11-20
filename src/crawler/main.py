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
    dbcreds = read_yaml('secrets/databases.yml').default
    dburl = build_connection_url(**dbcreds)

    engine = sa.create_engine(dburl, echo=True, future=True, connect_args={'options': '-csearch_path=common,public'})
    Base.metadata.create_all(engine, Base.metadata.tables.values(), checkfirst=True)

    # single check
    new_events = extract_all_events_tournament(tournament_id=41087, season=16)

    with Session(engine) as session:
        records = [EventsGlobal(**event) for event in new_events]
        session.add_all(records)
        session.commit()

    # while True:
    #     new_events = extract_all_events_tournament(tournament_id=41087, season=16)

    #     with Session(engine) as session:
    #         records = [EventsGlobal(**event) for event in new_events]
    #         session.add_all(records)
    #         session.commit()

    #     time.sleep(config.timeout)

if __name__ == '__main__':
    main()