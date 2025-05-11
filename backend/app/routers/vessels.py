from fastapi import APIRouter
from ..astronomy.vessels import PRESETS

router = APIRouter()

@router.get("/presets")
def get_vessel_presets():
  return PRESETS