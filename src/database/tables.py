from sqlalchemy import Column, Integer, String, ForeignKey, Boolean, Float
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

class TournamentScheduleHistory(Base):

    __tablename__ = 'tournament_calls_schedule_history'

    id = Column(Integer, primary_key=True, autoincrement=True)
    date_scheduled = Column(String(50))

# ---------------------------- #

class TeamDetails(Base):

    __tablename__ = 'team_details'

    team_id = Column(Integer, primary_key=True)
    picture_url = Column(String(100))

# ---------------------------- #

class PlayerDetails(Base):

    __tablename__ = 'player_details'

    player_id = Column(Integer, primary_key=True)
    picture_url = Column(String(100))

# ---------------------------- #

class EventResultsPlayerHistory(Base):

    __tablename__ = 'event_results_player_history'

    id = Column(Integer, primary_key=True)

    event_id = Column(Integer, ForeignKey('events_global.event_id'))
    event = relationship('EventsGlobal', backref='event_results_history_backref')

    #player_id = Column(Integer, ForeignKey('player_details.event_id'))
    #player = relationship('PlayerDetails', backref='player_details_backref')
    # f

    player_id = Column(Integer)
    sofascore = Column(Float, nullable=True)
