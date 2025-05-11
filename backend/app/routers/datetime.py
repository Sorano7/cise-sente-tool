from fastapi import APIRouter
from datetime import datetime, timezone

from ..custom_datetime.time import MeajiCalendar, ImorCalendar, JunesgiCalendar, standard_timestamp
from ..custom_datetime.date import MeajiCalendarDate, ImorCalendarDate, JunesgiCalendarDate, parse_date

router = APIRouter()

@router.get("/init")
def get_current_time():
  unix_timestamp = datetime.now(timezone.utc).timestamp()
  meaji_time = MeajiCalendarDate.from_timestamp(unix_timestamp)
  imor_time = ImorCalendarDate.from_timestamp(unix_timestamp)
  junesgi_time = JunesgiCalendarDate.from_timestamp(unix_timestamp)
  standard_time = standard_timestamp(unix_timestamp)
  
  return {
    "timestamp": standard_time,
    "meaji": {
      "segments": meaji_time.segments(),
      "separators": meaji_time.separators(),
      "rules": [None, None, None, None, 32, 9, 24, 24],
      "digits": [0, 1, 2, 0, 1, 1, 2, 2]
    },
    "imor": {
      "segments": imor_time.segments(),
      "separators": imor_time.separators(),
      "rules": [None, None, None, None, 18, 84, 48],
      "digits": [0, 1, 2, 2, 2, 2, 2]
    },
    "junesgi": {
      "segments": junesgi_time.segments(),
      "separators": junesgi_time.separators(),
      "rules": [None, None, None, 36, 9, 24, 24],
      "digits": [0, 1, 2, 2, 1, 2, 2]
    },
  }
  
@router.get("/convert")
def convert_time(timestamp: float):
  meaji_time = MeajiCalendarDate.from_timestamp(timestamp)
  imor_time = ImorCalendarDate.from_timestamp(timestamp)
  junesgi_time = JunesgiCalendarDate.from_timestamp(timestamp)
  standard_time = standard_timestamp(timestamp)
  
  return {
    "meaji": meaji_time.format_date(),
    "imor": imor_time.format_date(),
    "junesgi": junesgi_time.format_date(),
    "timestamp": f"{standard_time:.0f}"
  }

@router.get("/parse")
def parse_input_string(input: str):
  if not input.strip():
    timestamp = datetime.now().timestamp()
  else:
    timestamp = parse_date(input)

  return { "unix_timestamp": timestamp }