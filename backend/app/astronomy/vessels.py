from enum import Enum
from typing import Tuple
import math

from .utils import g_to_ms2

G_IN_MS2 = 9.81

class Vessel:
  def __init__(
    self,
    delta_v,
    mass_t,
    thrust_n
  ):
    self.delta_v = delta_v
    self.mass_t = mass_t
    self.thrust_n = thrust_n
    
  def max_distance_at(self, accel_g, dv=None):
    if not dv:
      dv = self.delta_v
    return (dv**2) / (4 * g_to_ms2(accel_g))
  
  def max_acceleration(self):
    mass_kg = self.mass_t * 1000
    return self.thrust_n / mass_kg
  
  def can_sustain(self, accel_g):
    return g_to_ms2(accel_g) <= self.max_acceleration()
  
  def can_reach(self, distance_m, accel_g, dv=None):
    return distance_m <= self.max_distance_at(accel_g, dv)

MULTI_PURPOSE = Vessel(delta_v=3300000, mass_t=175, thrust_n=1780000)

PRESETS = {
  "Micro-Fission Pulse": Vessel(delta_v=240000, mass_t=5000, thrust_n=1870000),
  "H-B Fusion": Vessel(delta_v=300000, mass_t=750, thrust_n=255000),
  "Plasma-Jet MIF CON": Vessel(delta_v=2100000, mass_t=175, thrust_n=1040000),
  "Plasma-Jet MIF OPT": Vessel(delta_v=3300000, mass_t=250, thrust_n=1780000),
  "Solid-Core NTR": Vessel(delta_v=7847, mass_t=100, thrust_n=1780000),
  "Gas-Core NTR Open-Cycle": Vessel(delta_v=108353, mass_t=125, thrust_n=2452500),
}