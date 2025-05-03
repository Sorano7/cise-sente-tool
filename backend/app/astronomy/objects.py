from enum import Enum
from typing import List
import math
from . import utils
from .utils import calculate_coordinate_relative_to_primary, move_towards

AU_IN_METER = 1.496e11
AU_IN_KM = 149597870.7
KM_IN_AU = 6.68459e-9
G = 6.67430e-11

class AstronomicalBody:
  """Represents an astronomical body"""

  def __init__(
      self, 
      name,
      radius_km,
      mass_kg,
      primary_object: 'AstronomicalBody' = None,
    ):
    self.name = name
    self.radius_km = radius_km
    self.mass_kg = mass_kg
    self.primary_object = primary_object
    
  def position_at_time(self, timestamp_second):
    raise NotImplementedError()
  
  def true_anomaly_at_time(self, timestamp):
    raise NotImplementedError()
  
  def safe_range(self):
    raise NotImplementedError()
    
class Star(AstronomicalBody):
  """Represents a star"""
  
  def __init__(self, name, radius_km, mass_kg, primary_object = None):
    super().__init__(name, radius_km, mass_kg, primary_object)
    
  def position_at_time(self, timestamp_second):
    return (0, 0, 0)
    
  def safe_range(self):
    return self.radius_km * 5 * 1000

class LagrangePoint(Enum):
  L1 = 1
  L2 = 2
  L3 = 3
  L4 = 4
  L5 = 5
   
class LagrangePointObject():
  def __init__(
    self,
    type: LagrangePoint,
    size_km,
    primary_object: AstronomicalBody,
    secondary_object: AstronomicalBody,
    semimajor_axis_au,
    eccentricity,
    inclination,
    longitude_of_ascending_node,
    argument_of_periapsis,
    mean_anomaly,
    name=None
  ):
    self.name = name
    self.type = type
    self.size_km = size_km
    self.primary_object = primary_object
    self.secondary_object = secondary_object
    self.semimajor_axis_au = semimajor_axis_au
    self.eccentricity = eccentricity
    self.inclination = inclination
    self.longitude_of_ascending_node = longitude_of_ascending_node
    self.argument_of_periapsis = argument_of_periapsis
    self.mean_anomaly = mean_anomaly
    
  def position_at_time(self, timestamp_second):
    """Return the coordinate of this object relative to the star"""
    
    coordinates = calculate_coordinate_relative_to_primary(
        self.semimajor_axis_au * AU_IN_METER,
        self.eccentricity,
        self.inclination,
        self.longitude_of_ascending_node,
        self.argument_of_periapsis,
        self.mean_anomaly,
        self.primary_object.mass_kg,
        timestamp_second
    )
    
    if self.type in (LagrangePoint.L3, LagrangePoint.L4, LagrangePoint.L5):
      offset = 0
    else:
      offset = self.size_km if self.type == LagrangePoint.L1 else -self.size_km
    
    offset *= KM_IN_AU 
      
    if isinstance(self.primary_object, Star):
      coordinates = move_towards(coordinates, (0, 0, 0), offset)
      return coordinates 
    elif isinstance(self.primary_object.primary_object, Star):
      x, y, z = self.primary_object.position_at_time(timestamp_second)
      rel_x, rel_y, rel_z = coordinates
      new_coordinates = move_towards((x + rel_x, y + rel_y, z + rel_z), (0, 0, 0), offset)
      return new_coordinates
    else:
      raise Exception("Invalid top-level primary object: Not a star")
    
  def true_anomaly_at_time(self, timestamp):
    mu = G * self.primary_object.mass_kg
    mean_motion = utils.compute_mean_motion(mu, self.semimajor_axis_au * AU_IN_METER)
    mean_anomaly = utils.compute_mean_anomaly_at_time(self.mean_anomaly, mean_motion, timestamp)
    eccentric_anomaly = utils.compute_eccentric_anomaly(self.eccentricity, mean_anomaly)
    true_anomaly = utils.compute_true_anomaly(self.eccentricity, eccentric_anomaly)
    
    return true_anomaly
  
  def safe_range(self):
    return None
      

class BasePlanet(AstronomicalBody):
  """Represent a planetary object such as a planet, a dwarf planet, or a moon"""

  def __init__(
      self,
      name,
      radius_km,
      mass_kg,
      semimajor_axis_au,
      axial_tilt,
      eccentricity,
      inclination,
      longitude_of_ascending_node,
      argument_of_periapsis,
      mean_anomaly,
      primary_object: AstronomicalBody,
    ):
    super().__init__(name, radius_km, mass_kg, primary_object)
    self.semimajor_axis_au = semimajor_axis_au
    self.axial_tilt = axial_tilt
    self.eccentricity = eccentricity
    self.inclination = inclination
    self.longitude_of_ascending_node = longitude_of_ascending_node
    self.argument_of_periapsis = argument_of_periapsis
    self.mean_anomaly = mean_anomaly
    
  def get_lagrange_points(self) -> List[LagrangePointObject]:
    """Return a list of lagrange points of this object"""
    
    mass_primary = self.primary_object.mass_kg
    mass_secondary = self.mass_kg
    a_au = self.semimajor_axis_au
    
    hill_radius_au = a_au * (mass_secondary / (3 * mass_primary))**(1/3)
    hill_radius_km = hill_radius_au * AU_IN_KM
    
    base_name = self.name[0:3]
    base_name = base_name.upper()
    
    return [
      LagrangePointObject(LagrangePoint.L1, hill_radius_km, self.primary_object, self, a_au, self.eccentricity, self.inclination, self.longitude_of_ascending_node, self.argument_of_periapsis, self.mean_anomaly, name=base_name+'-L1'),
      LagrangePointObject(LagrangePoint.L2, hill_radius_km, self.primary_object, self, a_au, self.eccentricity, self.inclination, self.longitude_of_ascending_node, self.argument_of_periapsis, self.mean_anomaly, name=base_name+'-L2'),
      LagrangePointObject(LagrangePoint.L3, hill_radius_km, self.primary_object, self, a_au, self.eccentricity, self.inclination, self.longitude_of_ascending_node, self.argument_of_periapsis, self.mean_anomaly - 180, name=base_name+'-L3'),
      LagrangePointObject(LagrangePoint.L4, hill_radius_km, self.primary_object, self, a_au, self.eccentricity, self.inclination, self.longitude_of_ascending_node, self.argument_of_periapsis, self.mean_anomaly + 60, name=base_name+'-L4'),
      LagrangePointObject(LagrangePoint.L5, hill_radius_km, self.primary_object, self, a_au, self.eccentricity, self.inclination, self.longitude_of_ascending_node, self.argument_of_periapsis, self.mean_anomaly - 60, name=base_name+'-L5')
    ]
    
  def get_orbital_period(self):
    """The orbital period in days"""

    mass_primary = self.primary_object.mass_kg
    a_m = self.semimajor_axis_au * AU_IN_METER
    
    orbital_period_seconds = 2 * math.pi * math.sqrt((a_m**3) / (G * mass_primary))
    ortbial_period_days = orbital_period_seconds / (24 * 3600)
    
    return ortbial_period_days
  
  def position_at_time(self, timestamp_second):
    """Return the coordinate of this object relative to the star"""
    
    coordinates = calculate_coordinate_relative_to_primary(
        self.semimajor_axis_au * AU_IN_METER,
        self.eccentricity,
        self.inclination,
        self.longitude_of_ascending_node,
        self.argument_of_periapsis,
        self.mean_anomaly,
        self.primary_object.mass_kg,
        timestamp_second
    )
    return coordinates 
  
  def true_anomaly_at_time(self, timestamp):
    mu = G * self.primary_object.mass_kg
    mean_motion = utils.compute_mean_motion(mu, self.semimajor_axis_au * AU_IN_METER)
    mean_anomaly = utils.compute_mean_anomaly_at_time(self.mean_anomaly, mean_motion, timestamp)
    eccentric_anomaly = utils.compute_eccentric_anomaly(self.eccentricity, mean_anomaly)
    true_anomaly = utils.compute_true_anomaly(self.eccentricity, eccentric_anomaly)
    
    return true_anomaly
  
  def safe_range(self):
    if self.radius_km is None:
      return None
    return self.radius_km * 1.2 * 1000
      
STAR = Star("Cise=Sente", 649119, 4.23e30)
    
class Planet(BasePlanet):
  """Represents a planet"""

  def __init__(self, name, radius_km, mass_kg, semimajor_axis_au, axial_tilt, eccentricity, inclination, longitude_of_ascending_node, argument_of_periapsis, mean_anomaly, primary_object: Star = STAR):
    super().__init__(name, radius_km, mass_kg, semimajor_axis_au, axial_tilt, eccentricity, inclination, longitude_of_ascending_node, argument_of_periapsis, mean_anomaly, primary_object)
  
class DwarfPlanet(BasePlanet):
  """Represents a dwarf planet"""

  def __init__(self, name, radius_km, mass_kg, semimajor_axis_au, axial_tilt, eccentricity, inclination, longitude_of_ascending_node, argument_of_periapsis, mean_anomaly, primary_object: Star = STAR):
    super().__init__(name, radius_km, mass_kg, semimajor_axis_au, axial_tilt, eccentricity, inclination, longitude_of_ascending_node, argument_of_periapsis, mean_anomaly, primary_object)
    
class Moon(BasePlanet):
  """Represents a nature satellite"""

  def __init__(self, name, radius_km, mass_kg, semimajor_axis_km, axial_tilt, eccentricity, inclination, longitude_of_ascending_node, argument_of_periapsis, mean_anomaly, primary_object: Planet):
    super().__init__(name, radius_km, mass_kg, semimajor_axis_km * KM_IN_AU, axial_tilt, eccentricity, inclination, longitude_of_ascending_node, argument_of_periapsis, mean_anomaly, primary_object)
 
  def position_at_time(self, timestamp_second):
    """Return the coordinate of this object relative to the star"""
    
    coordinates = calculate_coordinate_relative_to_primary(
        self.semimajor_axis_au * AU_IN_METER,
        self.eccentricity,
        self.inclination,
        self.longitude_of_ascending_node,
        self.argument_of_periapsis,
        self.mean_anomaly,
        self.primary_object.mass_kg,
        timestamp_second
    )
    
    x, y, z = self.primary_object.position_at_time(timestamp_second)
    rel_x, rel_y, rel_z = coordinates
    
    return (x + rel_x, y + rel_y, z + rel_z) 
  
  def current_phase(self, timestamp):
    """Calculate the phase fraction of this moon"""
    
    moon_pos = self.position_at_time(timestamp)
    primary_pos = self.primary_object.position_at_time(timestamp)
    
    moon_to_star = (
      0 - moon_pos[0],
      0 - moon_pos[1],
      0 - moon_pos[2]
    )
    
    moon_to_primary = (
      primary_pos[0] - moon_pos[0],
      primary_pos[1] - moon_pos[1],
      primary_pos[2] - moon_pos[2]
    )
    
    dot = sum(m * p for m, p in zip(moon_to_star, moon_to_primary))
    
    mag_star = math.sqrt(sum(m**2 for m in moon_to_star))
    mag_primary = math.sqrt(sum(p**2 for p in moon_to_primary))
    
    if mag_star == 0 or mag_primary == 0:
      return 0.0
    
    cos_phi = dot / (mag_star * mag_primary)
    cos_phi = max(-1.0, min(1.0, cos_phi))
    
    phi = math.acos(cos_phi)
    
    illumination = (1 + math.cos(phi)) / 2
    
    return illumination
    
       
PLANETS = {
  "Senawasa": Planet("Senawasa", 66445, 6.6e27, 0.0417, 3.4, 0.00151, 0.0175, 42.2, 270, -131),
  "Ihokronu": Planet("Ihokronu", 4224, 1.6e24, 0.168, 5.7, 0.0281, 0.0435, 214, 20.1, -60.7),
  "Kukkyo": Planet("Kukkyo", 7985, 2.3e25, 0.394, 32.1, 0.245, 0.0101, 182, 87, 173),
  "Junesgi": Planet("Junesgi", 58107, 1.35e27, 0.604, 57.6, 0.00279, 0, 0, 267, 84.1),
  "Ayurka": Planet("Ayurka", 5938, 4.64e24, 1.29, 19.2, 0.00177, 0.513, 125, 189, 148),
  "Iraska": Planet("Iraska", 7302, 2.47e24, 2.4, 29.4, 0.0307, 0.194, 266, 35.4, 171),
  "Noki Esfero": Planet("Noki Esfero", 25672, 1.36e26, 6.23, 22.2, 0.00413, 0.338, 98, 209, 10.9),
  "Gundemon": Planet("Gundemon", 104373, 7.8e27, 16.0, 67.1, 0.0312, 0.745, 317, 259, 144),
  "Seruna": Planet("Seruna", 42304, 1.75e27, 38.7, 45.4, 0.148, 2.97, 315, 0.792, -160)
}

DWARF_PLANETS = {
  # Tagiyo
  "Merua": DwarfPlanet("Merua", 468, 1.34e22, 3.76, 45.6, 0.0579, 3.56, 347, 233, -56.9),
  "Ixia": DwarfPlanet("Ixia", 716, 7.71e21, 4.14, 30.9, 0.0299, 0.0116, 27.7, 228, -37.3),
  "Akfane": DwarfPlanet("Akfane", 448, 1.85e21, 4.98, 14.5, 0.0273, 5.48, 1.11, 45.2, -107),
  "Casna": DwarfPlanet("Casna", 331, 6.73e20, 5.32, 43.8, 0.0469, 7.43, 132, 82.6, -172),
  
  # Kisekono
  "Yeaik": DwarfPlanet("Yeaik", 1032, 1.9e22, 18.4, 29.4, 0.0973, 13, 348, 236, -63),
  "Horta": DwarfPlanet("Horta", 884, 1.34e22, 24.5, 8.36, 0.122, 1.52, 44.9, 219, 110),
  "Gamio": DwarfPlanet("Gamio", 943, 1.73e22, 25.7, 6.97, 0.0462, 11.4, 353, 242, 96.4),
  
  # Uomo
  "Karmauk": DwarfPlanet("Karmauk", 960, 1.73e22, 62.8, 12.6, 0.179, 12.6, 22.1, 0, -140),
  "Oriciknes": DwarfPlanet("Oriciknes", 1150, 2.64e22, 103, 21.8, 0.392, 22.1, 83, 160, -58),
  "Kidixia": DwarfPlanet("Kidixia", 1350, 4.17e22, 188, 51.2, 0.512, 8.7, 22.1, 76.1, -52.6),
  "Opu Yu": DwarfPlanet("Opu Yu", 1580, 7.64e22, 639, 51.2, 0.766, 48.3, 0, 249, -13.2)
}

MOONS = {
  # Kukkyo
  "Tanau": Moon("Tanau", None, None, 86466, None, 0.00155, 0.253, 34.2, 182, 175, PLANETS["Kukkyo"]),
  "Ca": Moon("Ca", None, None, 125465, None, 0.00306, 0.0727, 278, 144, 47.9, PLANETS["Kukkyo"]),
  "Onno": Moon("Onno", None, None, 178689, None, 0.0544, 0.0399, 243, 359, -150, PLANETS["Kukkyo"]),
  
  # Junesgi
  "Usiek": Moon("Usiek", None, None, 212810, None, 0.000227, 0.281, 327, 133, 109, PLANETS["Junesgi"]),
  "Nesgada": Moon("Nesgada", None, None, 456840, None, 0.00313, 0.649, 44.9, 51.8, -175, PLANETS["Junesgi"]),
  
  # Ayurka
  "Haka": Moon("Haka", None, None, 266958, None, 0.00494, 0.2, 276, 191, -45.2, PLANETS["Ayurka"]),
  "Kerka": Moon("Kerka", None, None, 461834, None, 0.0232, 0.236, 154, 77.4, 33.4, PLANETS["Ayurka"]),

  # Iraska
  "Orione": Moon("Orione", None, None, 167815, None, 0.00126, 0.125, 267, 350, 0.466, PLANETS["Iraska"]),
  "Isune": Moon("Isune", None, None, 244280, None, 0.000914, 0.113, 64.6, 327, 169, PLANETS["Iraska"]),

  # Noki Esfero
  "Funisia": Moon("Funisia", None, None, 166115, None, 0.000397, 0.0117, 342, 270, -180, PLANETS["Noki Esfero"]),
  "Toku": Moon("Toku", None, None, 401156, None, 0.0002, 0.00429, 34.8, 270, 180, PLANETS["Noki Esfero"]),
  "Animaja": Moon("Animaja", None, None, 793670, None, 0.0, 0.0013, 338, 0, -55.8, PLANETS["Noki Esfero"]),

  # Gundemon
  "Eikkain": Moon("Eikkain", None, None, 460914, None, 0.0, 0.000883, 6.19, 145, 6.19, PLANETS["Gundemon"]),
  "Ahakain": Moon("Ahakain", None, None, 1805196, None, 0.0, 0.0055, 303, 0, 44.3, PLANETS["Gundemon"]),
  "Eraaik": Moon("Eraaik", None, None, 4433870, None, 0.0, 5.05, 277, 0.0, -110, PLANETS["Gundemon"]),
  "Noui": Moon("Noui", None, None, 6599255, None, 0.0, 0.47, 211, 0, -172, PLANETS["Gundemon"])
}

LAGRANGE_POINTS = {}

for planet in PLANETS.values():
  LPs = planet.get_lagrange_points()
  for point in LPs:
    orbit_name = planet.name[0:3]
    name = orbit_name.upper()
    LAGRANGE_POINTS[f"{name}-{point.type.name}"] = point
  
  
ALL_OBJECTS = {**PLANETS, **DWARF_PLANETS, **MOONS, **LAGRANGE_POINTS}