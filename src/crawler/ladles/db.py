from sqlalchemy import Column, Integer, String, TIMESTAMP
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import relationship

# ---------------------------- #

Base = declarative_base()

# ---------------------------- #

class EventsGlobal(Base):

    __tablename__ = 'events_global'

    event_id = Column(Integer, primary_key=True)
    start_timestamp = Column(Integer)
    round_num = Column(Integer)
    event_status_code = Column(Integer)
    event_status_type = Column(String(50))
    hometeam_id = Column(Integer)
    hometeam_name = Column(String(50))
    hometeam_namecode = Column(String(50))
    awayteam_id = Column(Integer)
    awayteam_name = Column(String(50))
    awayteam_namecode = Column(String(50))