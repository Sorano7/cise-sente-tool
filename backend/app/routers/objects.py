from fastapi import APIRouter, HTTPException
from ..astronomy.objects import ALL_OBJECTS, LagrangePointObject, LagrangePoint, Moon, DwarfPlanet
from typing import Dict, List

router = APIRouter()

@router.get("/")
def get_all_objects():
  return list(ALL_OBJECTS.keys())

@router.get("/positions")
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

@router.get("/position")
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