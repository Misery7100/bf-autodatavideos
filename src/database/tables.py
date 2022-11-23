from sqlalchemy import Column, Integer, String, ForeignKey, Boolean
from sqlalchemy.orm import declarative_base, relationship

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

# ---------------------------- #

# LineupsGlobal

# ---------------------------- #

class EventLineups(Base):
    
    __tablename__ = 'event_lineups'

    event_id = Column(Integer, ForeignKey('events_global.event_id'), primary_key=True)
    event = relationship('EventsGlobal', backref='event_lineups_backref')

    call_scheduled = Column(Boolean, default=False)
    scheduled_timestamp = Column(Integer, nullable=True)
    plainly_success = Column(Boolean, nullable=True)

# ---------------------------- #

class EventResults(Base):

    __tablename__ = 'event_results'

    event_id = Column(Integer, ForeignKey('events_global.event_id'), primary_key=True)
    event = relationship('EventsGlobal', backref='event_results_backref')
    call_scheduled = Column(Boolean, default=False)
    scheduled_timestamp = Column(Integer, nullable=True)
    plainly_success = Column(Boolean, nullable=True)

# ---------------------------- #