import time
import requests as rq

from typing import List, Dict, Any, Collection
from ..utils.common import DotDict

# ---------------------------- #

SOFASCORE_API = 'https://api.sofascore.com/api/v1'

# ---------------------------- #

def extract_one_page_events_tournament(tournament_id: int, season: int, page: int = 0) -> Collection[Dict[str, Any]]:
    
    url = f"{SOFASCORE_API}/unique-tournament/{season}/season/{tournament_id}/events/next/{page}"
    response = rq.get(url)
    data = response.json()

    parsed_events = list(map(parse_event_data, data['events']))
    has_next_page = data['hasNextPage']

    return parsed_events, has_next_page

# ---------------------------- #

def extract_all_events_tournament(tournament_id: int, season: int) -> Collection[Dict[str, Any]]:
    
    parsed_events = []
    has_next_page = True
    page = 0

    while has_next_page:
        new_page_events, has_next_page = extract_one_page_events_tournament(
                                            tournament_id=tournament_id, 
                                            season=season,
                                            page=page
                                        )
        parsed_events += new_page_events
        page += 1
        time.sleep(0.05)
    
    return parsed_events

# ---------------------------- #

def parse_event_data(event: dict) -> Dict[str, Any]:

    # dot access
    event = DotDict(event)
    
    event_id = event.id
    start_timestamp = event.startTimestamp
    round_num = event.roundInfo.round
    event_status_code = event.status.code
    event_status_type = event.status.type
    hometeam_id = event.homeTeam.id
    hometeam_name = event.homeTeam.name
    hometeam_namecode = event.homeTeam.nameCode
    awayteam_id = event.awayTeam.id
    awayteam_name = event.awayTeam.name
    awayteam_namecode = event.awayTeam.nameCode

    record = dict(
        event_id=event_id,
        start_timestamp=start_timestamp,
        round_num=round_num,
        event_status_code=event_status_code,
        event_status_type=event_status_type,
        hometeam_id=hometeam_id,
        hometeam_name=hometeam_name,
        hometeam_namecode=hometeam_namecode,
        awayteam_id=awayteam_id,
        awayteam_name=awayteam_name,
        awayteam_namecode=awayteam_namecode
    )

    return record