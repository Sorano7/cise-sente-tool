EPOCH_TO_UNIX_EPOCH_OFFSET = 23164249536

class BaseCalendar:
  def __init__(self):
    pass
  
  def seconds_to_duration(self, seconds):
    raise NotImplementedError()
  
  def duration_to_seconds(self):
    raise NotImplementedError()
  
  def year_type(self, year):
    raise NotImplementedError()
  
  def month_cycle(self, year):
    raise NotImplementedError()
  
  def days_up_to_month(self, month, year=None):
    raise NotImplementedError()
  
class MeajiCalendar(BaseCalendar):
  SECONDS_PER_MINUTE = 24
  MINUTES_PER_SUBHOUR = 24
  SUBHOUR_PER_HOUR = 9
  HOURS_PER_DAY = 32
  
  SECONDS_PER_SUBHOUR = SECONDS_PER_MINUTE * MINUTES_PER_SUBHOUR
  SECONDS_PER_HOUR = SECONDS_PER_SUBHOUR * SUBHOUR_PER_HOUR
  SECONDS_PER_DAY = SECONDS_PER_HOUR * HOURS_PER_DAY
  
  DAYS_PER_REGULAR_YEAR = 190
  DAYS_PER_FULL_YEAR_CYCLE = DAYS_PER_REGULAR_YEAR * 4 + 1
  
  REGULAR_MONTH_CYCLE = [21, 21, 21, 21, 21, 21, 21, 21, 22]
  LEAP_MONTH_CYCLE = [21, 21, 21, 22, 21, 21, 21, 21, 22]
  
  ELAPSED_SECONDS_AT_EPOCH = 101174242752
  
  QUARTERS = ['Fu', 'Se', 'Myu', 'Jo']
  
  DAYS_PER_WEEK = 9
  
  def __init__(self):
    pass
  
  def seconds_to_duration(self, seconds):
    days, rem = divmod(seconds, self.SECONDS_PER_DAY)
    hours, rem = divmod(rem, self.SECONDS_PER_HOUR)
    sub_hours, rem = divmod(rem, self.SECONDS_PER_SUBHOUR)
    minutes, seconds = divmod(rem, self.SECONDS_PER_MINUTE)
    return days, hours, sub_hours, minutes, seconds
  
  def duration_to_seconds(self, days=0, hours=0, sub_hours=0, minutes=0, seconds=0):
    return (
      days * self.SECONDS_PER_DAY +
      hours * self.SECONDS_PER_HOUR +
      sub_hours * self.SECONDS_PER_SUBHOUR +
      minutes * self.SECONDS_PER_MINUTE +
      seconds
    )
    
  def year_type(self, year):
    return "leap" if self.is_leap_year(year) else "regular"
  
  def is_leap_year(self, year):
    return (year == 0) or (year % 4 == 0 and year % 60 != 0)
  
  def month_cycle(self, year):
    return self.LEAP_MONTH_CYCLE if self.is_leap_year(year) else self.REGULAR_MONTH_CYCLE
  
  def days_up_to_month(self, month, year=None):
    month_cycle = self.REGULAR_MONTH_CYCLE
    if year is not None:
      month_cycle = self.month_cycle(year)
      
    return sum(month_cycle[:month - 1])
  
  def absolute_hour(self, quarter, relative_hour):
    quarter_idx = self.QUARTERS.index(quarter)
    absolute_hour = quarter_idx * 8 + relative_hour
    
    return absolute_hour
  
  def quarter_relative_hour(self, hour):
    quarter = self.QUARTERS[hour // 8]
    relative_hour = hour % 8
    
    return quarter, relative_hour
  
  def separators(self):
    return ["=", ".", ", ", "=", ".", ", ", "."]
  
class ImorCalendar(BaseCalendar):
  SECONDS_PER_MINUTE = 48
  MINUTES_PER_HOUR = 84
  HOURS_PER_DAY = 18
  
  SECONDS_PER_HOUR = SECONDS_PER_MINUTE * MINUTES_PER_HOUR
  SECONDS_PER_DAY = SECONDS_PER_HOUR * HOURS_PER_DAY
  
  DAYS_PER_REGULAR_YEAR = 1108
  DAYS_PER_FULL_YEAR_CYCLE = DAYS_PER_REGULAR_YEAR * 2 + 1
  
  REGULAR_SUB_YEAR_CYCLE = [277, 277, 277, 277]
  LEAP_SUB_YEAR_CYCLE = [277, 277, 277, 278]
  DROP_SUB_YEAR_CYCLE = [277, 277, 277, 276]
  
  REGULAR_MONTH_CYCLE = [40, 39, 40, 39, 40, 39, 40]
  LEAP_MONTH_CYCLE = [40, 39, 40, 39, 40, 39, 41]
  DROP_MONTH_CYCLE = [40, 39, 40, 39, 40, 39, 39]
  
  ELAPSED_SECONDS_AT_EPOCH = EPOCH_TO_UNIX_EPOCH_OFFSET
  
  DAYS_PER_WEEK = 6
  
  def __init__(self):
    super().__init__()
    
  def seconds_to_duration(self, seconds):
    days, rem = divmod(seconds, self.SECONDS_PER_DAY)
    hours, rem = divmod(rem, self.SECONDS_PER_HOUR)
    minutes, seconds = divmod(rem, self.SECONDS_PER_MINUTE)
    return days, hours, minutes, seconds
  
  def duration_to_seconds(self, days=0, hours=0, minutes=0, seconds=0):
    return (
      days * self.SECONDS_PER_DAY +
      hours * self.SECONDS_PER_HOUR +
      minutes * self.SECONDS_PER_MINUTE + 
      seconds
    )
  
  def year_type(self, year):
    if year % 50 == 0:
      return "drop"
    elif year % 2 == 0:
      return "leap"
    else:
      return "regular"
  
  def month_cycle(self, year):
    year_type = self.year_type(year)
    
    match year_type:
      case "drop":
        return self.DROP_MONTH_CYCLE
      case "leap":
        return self.LEAP_MONTH_CYCLE
      case "regular":
        return self.REGULAR_MONTH_CYCLE
      
  def sub_year_cycle(self, year):
    year_type = self.year_type(year)
    
    match year_type:
      case "drop":
        return self.DROP_SUB_YEAR_CYCLE
      case "leap":
        return self.LEAP_SUB_YEAR_CYCLE
      case "regular":
        return self.REGULAR_SUB_YEAR_CYCLE
  
  def days_up_to_month(self, month, year=None):
    month_cycle = self.REGULAR_MONTH_CYCLE
    if year is not None:
      month_cycle = self.month_cycle(year)
      
    return sum(month_cycle[:month - 1])
  
  def days_up_to_sub_year(self, sub_year, year=None):
    sub_year_cycle = self.REGULAR_SUB_YEAR_CYCLE
    if year is not None:
      sub_year_cycle = self.sub_year_cycle(year)
      
    return sum(sub_year_cycle[:sub_year - 1]) 
  
  def separators(self):
    return [".", "=", ", ", ".", ", ", "."]
  
class JunesgiCalendar:
  SECONDS_PER_MINUTE = 24
  MINUTES_PER_SUBHOUR = 24
  SUBHOUR_PER_HOUR = 9
  HOURS_PER_DAY = 36
  
  SECONDS_PER_SUBHOUR = SECONDS_PER_MINUTE * MINUTES_PER_SUBHOUR
  SECONDS_PER_HOUR = SECONDS_PER_SUBHOUR * SUBHOUR_PER_HOUR
  SECONDS_PER_DAY = SECONDS_PER_HOUR * HOURS_PER_DAY
  
  REGULAR_YEAR_CYCLE = [54, 55, 54, 55]
  LEAP_YEAR_CYCLE = [54, 55, 55, 55]
  
  DAYS_PER_REGULAR_SUPER_YEAR = 218
  DAYS_PER_FULL_SUPER_YEAR_CYCLE = DAYS_PER_REGULAR_SUPER_YEAR * 3 + 1
  
  ELAPSED_SECONDS_AT_EPOCH = EPOCH_TO_UNIX_EPOCH_OFFSET
  
  DAYS_PER_WEEK = 9
  
  def __init__(self):
    pass
  
  def seconds_to_duration(self, seconds):
    days, rem = divmod(seconds, self.SECONDS_PER_DAY)
    hours, rem = divmod(rem, self.SECONDS_PER_HOUR)
    sub_hours, rem = divmod(rem, self.SECONDS_PER_SUBHOUR)
    minutes, seconds = divmod(rem, self.SECONDS_PER_MINUTE)
    return days, hours, sub_hours, minutes, seconds
  
  def duration_to_seconds(self, days=0, hours=0, sub_hours=0, minutes=0, seconds=0):
    return (
      days * self.SECONDS_PER_DAY +
      hours * self.SECONDS_PER_HOUR +
      sub_hours * self.SECONDS_PER_SUBHOUR +
      minutes * self.SECONDS_PER_MINUTE +
      seconds
    )
  
  def year_type(self, year):
    return "leap" if self.is_leap_year(year) else "regular"
  
  def is_leap_year(self, year):
    return year % 3 == 0 and year % 16 != 0
  
  def year_cycle(self, super_year):
    return self.LEAP_YEAR_CYCLE if self.is_leap_year(super_year) else self.REGULAR_YEAR_CYCLE
  
  def days_up_to_year(self, year, super_year=None):
    year_cycle = self.REGULAR_YEAR_CYCLE
    if super_year is not None:
      year_cycle = self.year_cycle(super_year)
    return sum(year_cycle[:year - 1])
  
  def separators(self):
    return ["=", ".", ", ", ".", ", ", "."]
  
def standard_timestamp(unix_timestamp):
  return unix_timestamp + EPOCH_TO_UNIX_EPOCH_OFFSET