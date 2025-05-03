from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware

from .astronomy.objects import ALL_OBJECTS, LagrangePointObject, LagrangePoint, Moon, DwarfPlanet
from .astronomy.vessels import Vessel, PRESETS
from .astronomy.pathfinder import PathFinder, Policy

from .custom_datetime.time import MeajiCalendar, ImorCalendar, JunesgiCalendar, standard_timestamp
from .custom_datetime.date import MeajiCalendarDate, ImorCalendarDate, JunesgiCalendarDate, parse_date
from datetime import datetime, timezone

from typing import Dict, List

app = FastAPI()

app.add_middleware(
  CORSMiddleware,
  allow_origins=["*"],
  allow_credentials=True,
  allow_methods=["*"],
  allow_headers=["*"]
)

@app.get("/api/positions")
def get_positions(timestamp: float) -> Dict[str, Dict]:
  """Return all object positions at a given timestamp."""
  positions = {}
  for name, obj in ALL_OBJECTS.items():
    pos = obj.position_at_time(timestamp) 
    if isinstance(obj, Moon):
      primary_obj = obj.primary_object.name
      obj_type = f"orbital_{primary_obj}"
    elif isinstance(obj, LagrangePointObject):
      secondary_obj = obj.secondary_object.name
      if obj.type in (LagrangePoint.L1, LagrangePoint.L2):
        obj_type = f"lagrange_orbital_{secondary_obj}"
      else:
        obj_type = 'lagrange'
    elif isinstance(obj, DwarfPlanet):
      obj_type = "dwarf"
    else:
      obj_type = "planet"
      
    a = getattr(obj, "semimajor_axis_au", None)
    
    positions[name] = {
      "x": pos[0],
      "y": pos[1],
      "z": pos[2],
      "type": obj_type,
      "a": a
    }
  return positions

@app.get("/api/objects")
def get_all_objects():
  return list(ALL_OBJECTS.keys())

@app.get("/api/position")
def get_position(name: str, timestamp: float):
    obj = ALL_OBJECTS.get(name)
    if not obj:
        raise HTTPException(status_code=404, detail="Object not found")
    
    pos = obj.position_at_time(timestamp)
    return {
        "x": pos[0],
        "y": pos[1],
        "z": pos[2]
    }
    
    
class VesselInput(BaseModel):
    delta_v: float
    mass_t: float
    thrust_n: float

class PolicyInput(BaseModel):
    time_weight: float
    cost_weight: float
    comfort_weight: float
    disable_coast: bool = False

class PathfindRequest(BaseModel):
    vessel: VesselInput
    policy: PolicyInput
    origin: str
    destination: str
    launch_time: float
    mandatory_stops: List[str]
    
@app.post("/api/pathfind")
def pathfind(request: PathfindRequest):
    origin_obj = ALL_OBJECTS.get(request.origin)
    destination_obj = ALL_OBJECTS.get(request.destination)
    mandatory_stops = [ALL_OBJECTS.get(s) for s in request.mandatory_stops] 
    stops_string = "<direct>"
    if mandatory_stops:
      stops_string = " -> ".join(request.mandatory_stops)
    
      
    print(f"[pathfind] Path find {origin_obj.name} -> {stops_string} -> {destination_obj.name}")

    if origin_obj is None or destination_obj is None:
        raise HTTPException(status_code=400, detail="Invalid origin or destination name.")

    vessel = Vessel(
        delta_v=request.vessel.delta_v,
        mass_t=request.vessel.mass_t,
        thrust_n=request.vessel.thrust_n
    )

    policy = Policy(
        time_weight=request.policy.time_weight,
        cost_weight=request.policy.cost_weight,
        comfort_weight=request.policy.comfort_weight,
        disable_coast=request.policy.disable_coast
    )
    
    pathfinder = PathFinder(vessel, policy, list(ALL_OBJECTS.values()))
    pathfinder.find_path(origin_obj, destination_obj, request.launch_time, mandatory_stops)
    return pathfinder.parse_path()
  
@app.get("/api/vessels/presets")
def get_vessel_presets():
  return PRESETS

@app.get("/api/datetime/init")
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
  
@app.get("/api/datetime/convert")
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

@app.get("/api/datetime/parse")
def parse_input_string(input: str):
  if not input.strip():
    timestamp = datetime.now().timestamp()
  else:
    timestamp = parse_date(input)

  return { "unix_timestamp": timestamp }