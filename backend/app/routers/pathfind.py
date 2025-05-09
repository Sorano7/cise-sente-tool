from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ..astronomy.objects import ALL_OBJECTS
from ..astronomy.vessels import Vessel
from ..astronomy.pathfinder import PathFinder, Policy

from typing import List

router = APIRouter()

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
    
@router.post("/")
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