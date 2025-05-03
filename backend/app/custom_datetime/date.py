from .utils import count_cycle
from .time import BaseCalendar, MeajiCalendar, ImorCalendar, JunesgiCalendar
from datetime import datetime
import re

class BaseDate:
  def __init__(self):
    self.calendar: BaseCalendar = None 
    pass
  
  def to_earth_date(self) -> datetime:
    timestamp = self.elapsed_seconds_since_epoch()
    earth_date = datetime.fromtimestamp(timestamp)
    
    return earth_date
  
  def week_day_index(self) -> int:
    total_seconds = self.elapsed_seconds_since_epoch()
    total_days = total_seconds // self.calendar.SECONDS_PER_DAY
    return total_days % self.calendar.DAYS_PER_WEEK + 1
  
  def total_seconds(self) -> int:
    raise NotImplementedError()
  
  def elapsed_seconds_since_epoch(self) -> int:
    total_seconds = self.total_seconds()
    return total_seconds - self.calendar.ELAPSED_SECONDS_AT_EPOCH
  
  def format_date(self) -> str:
    raise NotImplementedError()
  
  def segments(self):
    raise NotImplementedError()
  
  def separators(self):
    raise NotImplementedError()
  
  
  @classmethod
  def from_timestamp(cls, elapsed_seconds):
    raise NotImplementedError()
  
  @classmethod
  def from_formatted_string(cls, date_string: str):
    raise NotImplementedError()
  
  @classmethod
  def from_earth_date(cls, earth_date: datetime):
    elapsed_seconds = earth_date.timestamp()
    return cls.from_timestamp(elapsed_seconds)
  

class MeajiCalendarDate(BaseDate):
  def __init__(
    self,
    year,
    month,
    day,
    hour,
    sub_hour,
    minute,
    second
  ):
    self.year = year
    self.month = month
    self.day = day
    self.hour = hour
    self.sub_hour = sub_hour
    self.minute = minute
    self.second = second
    
    self.calendar = MeajiCalendar()
    
  def total_seconds(self) -> int:
    """Total seconds since year 0"""
    
    total_seconds = 0
    
    # Year
    full_year_cycles, remaining_years = divmod(self.year, 4)
    total_seconds += self.calendar.duration_to_seconds(days=full_year_cycles * self.calendar.DAYS_PER_FULL_YEAR_CYCLE)
    total_seconds += self.calendar.duration_to_seconds(days=self.calendar.DAYS_PER_REGULAR_YEAR + 1) # Year 0
    total_seconds += self.calendar.duration_to_seconds(days=remaining_years * self.calendar.DAYS_PER_REGULAR_YEAR)
    
    # Remove extra leap days
    extra_days = self.year // 60
    total_seconds -= self.calendar.duration_to_seconds(days=extra_days)
    
    # Month
    total_seconds += self.calendar.duration_to_seconds(days=self.calendar.days_up_to_month(self.month, self.year))
    
    # Adjust by 1
    total_seconds += self.calendar.duration_to_seconds(days=self.day - 1)
    
    # Min value is 0, add directly
    total_seconds += self.calendar.duration_to_seconds(hours=self.hour, sub_hours=self.sub_hour, minutes=self.minute, seconds=self.second)
    
    return total_seconds
  
  def format_date(self) -> str:
    """Return a formatted string of this date"""
    
    quarter, rel_hour = self.calendar.quarter_relative_hour(self.hour)
    
    return f'{self.year}={self.month}.{str(self.day).zfill(2)}, {quarter}={rel_hour}.{self.sub_hour}, {str(self.minute).zfill(2)}.{str(self.second).zfill(2)}'
  
  @classmethod
  def from_timestamp(cls, elapsed_seconds):
    calendar = MeajiCalendar()
    # Adjust for epoch
    elapsed_seconds += calendar.ELAPSED_SECONDS_AT_EPOCH
    
    # Year
    full_year_cycles, remaining_seconds = divmod(elapsed_seconds, calendar.duration_to_seconds(days=calendar.DAYS_PER_FULL_YEAR_CYCLE))
    remaining_seconds -= calendar.duration_to_seconds(days=calendar.DAYS_PER_REGULAR_YEAR + 1) # Adjust for year 0
    
    # Handle leap days
    extra_days = (full_year_cycles * 4) // 60
    remaining_seconds += calendar.duration_to_seconds(days=extra_days)
    
    remaining_years, remaining_seconds = divmod(remaining_seconds, (calendar.DAYS_PER_REGULAR_YEAR * calendar.SECONDS_PER_DAY))
    
    year = full_year_cycles * 4 + remaining_years
    
    # Month
    current_month_cycle = calendar.month_cycle(year)
    month = count_cycle(current_month_cycle, remaining_seconds, calendar.SECONDS_PER_DAY)
    remaining_seconds -= calendar.duration_to_seconds(days=calendar.days_up_to_month(month, year))
    
    # Rest
    day, hour, sub_hour, minute, second = calendar.seconds_to_duration(remaining_seconds)
    day += 1
    
    return cls(int(year), int(month), int(day), int(hour), int(sub_hour), int(minute), int(second))
    
  @classmethod
  def from_formatted_string(cls, date_string: str):
    calendar = MeajiCalendar()
    try:
      # Split into parts
      date, time_upper, time_lower = date_string.split(", ")
      
      # Parse date
      year_month, day = date.split(".")
      year, month = year_month.split("=")
      
      # Parse upper time (hour, sub_hour)
      quarter, rel_hour_subhour = time_upper.split("=")
      rel_hour, sub_hour = rel_hour_subhour.split(".")
      
      # Parse lower time (minute, second)
      minute, second = time_lower.split(".")
      
      year = int(year)
      month = int(month)
      day = int(day)
      rel_hour = int(rel_hour)
      sub_hour = int(sub_hour)
      minute = int(minute)
      second = int(second)
      
      absolute_hour = calendar.absolute_hour(quarter, rel_hour)
      
      return cls(year, month, day, absolute_hour, sub_hour, minute, second)
    
    except Exception as e:
      return None
    
  def segments(self):
    return [self.year, self.month, self.day, -1, self.hour, self.sub_hour, self.minute, self.second]
  
  def separators(self):
    return ["=", ".", ", ", "=", ".", ", ", "."]
    
class ImorCalendarDate(BaseDate):
  def __init__(
    self,
    year,
    sub_year,
    month,
    day,
    hour,
    minute,
    second
  ):
    self.year = year
    self.sub_year = sub_year
    self.month = month
    self.day = day
    self.hour = hour
    self.minute = minute
    self.second = second
    
    self.calendar: ImorCalendar = ImorCalendar()
  
  def total_seconds(self) -> int:
    total_seconds = 0
    
    # Year
    full_year_cycles, remaining_years = divmod(self.year, 2)
    total_seconds += self.calendar.duration_to_seconds(days=full_year_cycles * self.calendar.DAYS_PER_FULL_YEAR_CYCLE)
    total_seconds += self.calendar.duration_to_seconds(days=remaining_years * self.calendar.DAYS_PER_REGULAR_YEAR)
    
    extra_days = self.year // 50 * 2
    total_seconds -= self.calendar.duration_to_seconds(days=extra_days)
    
    # Sub year & Month
    total_seconds += self.calendar.duration_to_seconds(days=self.calendar.days_up_to_sub_year(self.sub_year, self.year))
    total_seconds += self.calendar.duration_to_seconds(days=self.calendar.days_up_to_month(self.month, self.year))
    
    # Adjust by 1
    total_seconds += self.calendar.duration_to_seconds(days=self.day - 1)
  
    total_seconds += self.calendar.duration_to_seconds(hours=self.hour, minutes=self.minute, seconds=self.second)
    
    return total_seconds
  
  def format_date(self) -> str:
    return f'{self.year}.{self.sub_year}={self.month}.{str(self.day).zfill(2)}, {str(self.hour).zfill(2)}.{str(self.minute).zfill(2)}.{str(self.second).zfill(2)}'
  
  @classmethod
  def from_timestamp(cls, elapsed_seconds):
    calendar = ImorCalendar()
    elapsed_seconds += calendar.ELAPSED_SECONDS_AT_EPOCH
    
    full_year_cycles, remaining_seconds = divmod(elapsed_seconds, (calendar.duration_to_seconds(days=calendar.DAYS_PER_FULL_YEAR_CYCLE)))
  
    extra_days = ((full_year_cycles * 2) // 50) * 2
    remaining_seconds += calendar.duration_to_seconds(days=extra_days)
    
    remaining_year, remaining_seconds = divmod(remaining_seconds, (calendar.duration_to_seconds(days=calendar.DAYS_PER_REGULAR_YEAR)))
    
    year = full_year_cycles * 2 + remaining_year
    
    current_sub_year_cycle = calendar.sub_year_cycle(year)
    sub_year = count_cycle(current_sub_year_cycle, remaining_seconds, calendar.SECONDS_PER_DAY)
    remaining_seconds -= calendar.duration_to_seconds(days=calendar.days_up_to_sub_year(sub_year, year))
    
    current_month_cycle = calendar.month_cycle(year)
    month = count_cycle(current_month_cycle, remaining_seconds, calendar.SECONDS_PER_DAY)
    remaining_seconds -= calendar.duration_to_seconds(days=calendar.days_up_to_month(month, year))
    
    day, hour, minute, second = calendar.seconds_to_duration(remaining_seconds)
    day += 1
    
    return cls(int(year), int(sub_year), int(month), int(day), int(hour), int(minute), int(second))

  @classmethod
  def from_formatted_string(cls, date_string: str): 
    try:
      date, time = date_string.split(", ")
      year_sub_year, month_day = date.split("=")
      year, sub_year = year_sub_year.split(".")
      month, day = month_day.split(".")
      
      hour, minute, second = time.split(".")
      
      return cls(int(year), int(sub_year), int(month), int(day), int(hour), int(minute), int(second))
    except:
      return None
  
  def segments(self):
    return [self.year, self.sub_year, self.month, self.day, self.hour, self.minute, self.second]
  
  def separators(self):
    return [".", "=", ", ", ".", ", ", "."]
  
class JunesgiCalendarDate(BaseDate):
  def __init__(
    self,
    super_year,
    year,
    day,
    hour,
    sub_hour,
    minute,
    second
  ):
    self.super_year = super_year
    self.year = year
    self.day = day
    self.hour = hour
    self.sub_hour = sub_hour
    self.minute = minute
    self.second = second
    
    self.calendar: JunesgiCalendar = JunesgiCalendar() 
  
  def total_seconds(self) -> int:
    total_seconds = 0
    
    full_super_year_cycles, remaining_super_years = divmod(self.super_year, 3)
    total_seconds += self.calendar.duration_to_seconds(days=full_super_year_cycles * self.calendar.DAYS_PER_FULL_SUPER_YEAR_CYCLE)
    total_seconds += self.calendar.duration_to_seconds(days=remaining_super_years * self.calendar.DAYS_PER_REGULAR_SUPER_YEAR)
    
    extra_days = self.super_year // 16
    total_seconds -= self.calendar.duration_to_seconds(days=extra_days)
    
    total_seconds += self.calendar.duration_to_seconds(days=self.calendar.days_up_to_year(self.year, self.super_year))
    
    total_seconds += self.calendar.duration_to_seconds(days=self.day - 1)
    total_seconds += self.calendar.duration_to_seconds(hours=self.hour, sub_hours=self.sub_hour, minutes=self.minute, seconds=self.second)
    
    return total_seconds
  
  def format_date(self) -> str:
    return f'{self.super_year}={self.year}.{str(self.day).zfill(2)}, {str(self.hour).zfill(2)}.{self.sub_hour}, {str(self.minute).zfill(2)}.{str(self.second).zfill(2)}'
  
  @classmethod
  def from_timestamp(cls, elapsed_seconds):
    calendar = JunesgiCalendar()
    elapsed_seconds += calendar.ELAPSED_SECONDS_AT_EPOCH
    
    full_super_year_cycles, remaining_seconds = divmod(elapsed_seconds, calendar.duration_to_seconds(days=calendar.DAYS_PER_FULL_SUPER_YEAR_CYCLE))
    
    extra_days = (full_super_year_cycles * 3) // 16
    remaining_seconds += calendar.duration_to_seconds(days=extra_days)
    
    remaining_super_years, remaining_seconds = divmod(remaining_seconds, calendar.duration_to_seconds(days=calendar.DAYS_PER_REGULAR_SUPER_YEAR))
    
    super_year = full_super_year_cycles * 3 + remaining_super_years
    
    current_year_cycle = calendar.year_cycle(super_year)
    year = count_cycle(current_year_cycle, remaining_seconds, calendar.SECONDS_PER_DAY)
    remaining_seconds -= calendar.duration_to_seconds(days=calendar.days_up_to_year(year, super_year))
    
    day, hour, sub_hour, minute, second = calendar.seconds_to_duration(remaining_seconds)
    day += 1
    
    return cls(int(super_year), int(year), int(day), int(hour), int(sub_hour), int(minute), int(second))
  
  @classmethod
  def from_formatted_string(cls, date_string: str):
    try:
      date, time_upper, time_lower = date_string.split(", ")
      
      super_year, year_day = date.split("=")
      year, day = year_day.split(".")
      
      hour, sub_hour = time_upper.split(".")
      minute, second = time_lower.split(".")
      
      return cls(int(super_year), int(year), int(day), int(hour), int(sub_hour), int(minute), int(second))
    except:
      return None
  
  def segments(self):
    return [self.super_year, self.year, self.day, self.hour, self.sub_hour, self.minute, self.second]
  
  def separators(self):
    return ["=", ".", ", ", ".", ", ", "."]
  
  
def parse_date(date: str):
  timestamp = 0
  if is_int(date):
    timestamp = int(date) - 23164249536
    return timestamp
  
  for calendar in [MeajiCalendarDate, ImorCalendarDate, JunesgiCalendarDate]:
    date_obj = calendar.from_formatted_string(date)
    if date_obj:
      timestamp = date_obj.elapsed_seconds_since_epoch()
      return timestamp
  return None
  
    
def is_int(s):
  try:
    int(s)
    return True
  except ValueError:
    return False
  
  
