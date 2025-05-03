import math
import numpy as np
from typing import Tuple

G = 6.67430e-11

G_IN_MS2 = 9.81
AU_IN_METER = 1.496e11

def calculate_coordinate_relative_to_primary(
  semimajor_axis_m,
  eccentricity,
  inclination,
  longitude_of_ascending_node,
  argument_of_periapsis,
  mean_anomaly_at_epoch,
  mass_primary_kg,
  elapsed_seconds
) -> Tuple[float, float, float]:
  """Calculate the 3D coordinate relative to a primary object"""
  
  # Convert angles to radians
  inclination = math.radians(inclination)
  longitude_of_ascending_node = math.radians(longitude_of_ascending_node)
  argument_of_periapsis = math.radians(argument_of_periapsis)
  mean_anomaly_at_epoch = math.radians(mean_anomaly_at_epoch)
  
  mu = G * mass_primary_kg
  
  # Mean motion in radians per second
  mean_motion = math.sqrt(mu / semimajor_axis_m**3)
  
  # Mean anomaly at given timestamp
  mean_anomaly = mean_anomaly_at_epoch + mean_motion * elapsed_seconds
  
  eccentric_anomaly = compute_eccentric_anomaly(eccentricity, mean_anomaly) 
  true_anomaly = compute_true_anomaly(eccentricity, eccentric_anomaly)
  
  distance = semimajor_axis_m * (1 - eccentricity * math.cos(eccentric_anomaly))
  
  orbital_x = distance * math.cos(true_anomaly)
  orbital_y = distance * math.sin(true_anomaly)
  
  # To 3D
  # Rotate by argument of periapsis
  x1 = orbital_x * math.cos(argument_of_periapsis) - orbital_y * math.sin(argument_of_periapsis)
  y1 = orbital_x * math.sin(argument_of_periapsis) + orbital_y * math.cos(argument_of_periapsis)
  z1 = 0
  
  # Rotate by inclination
  x2 = x1
  y2 = y1 * math.cos(inclination)
  z2 = y1 * math.sin(inclination)
  
  # Rotate by longitude of ascending node
  x = x2 * math.cos(longitude_of_ascending_node) - y2 * math.sin(longitude_of_ascending_node)
  y = x2 * math.sin(longitude_of_ascending_node) + y2 * math.cos(longitude_of_ascending_node)
  z = z2
  
  # Convert to AU
  return (x / AU_IN_METER, y / AU_IN_METER, z / AU_IN_METER)

def compute_mean_motion(mu, semimajor_axis_m):
  return math.sqrt(mu / semimajor_axis_m**3)

def compute_mean_anomaly_at_time(mean_anomaly_at_epoch, mean_motion, elapsed_seconds):
  return mean_anomaly_at_epoch + mean_motion * elapsed_seconds

def compute_eccentric_anomaly(eccentricity, mean_anomaly):
  eccentric_anomaly = mean_anomaly
  for _ in range(100):
    delta = (eccentric_anomaly - eccentricity * math.sin(eccentric_anomaly) - mean_anomaly) / (1 - eccentricity * math.cos(eccentric_anomaly))
    eccentric_anomaly -= delta
    if abs(delta) < 1e-6:
        break
  return eccentric_anomaly

def compute_true_anomaly(eccentricity, eccentric_anomaly):
  true_anomaly = 2 * math.atan2(
    math.sqrt(1 + eccentricity) * math.sin(eccentric_anomaly / 2),
    math.sqrt(1 - eccentricity) * math.cos(eccentric_anomaly / 2)
  )
  
  return true_anomaly

def distance_at_time(a, b, timestamp):
  a_pos = a.position_at_time(timestamp)
  b_pos = b.position_at_time(timestamp)
  return linear_distance(a_pos, b_pos) * AU_IN_METER

def linear_distance(src_pos, dst_pos):
 return math.sqrt(
    (dst_pos[0] - src_pos[0])**2 +
    (dst_pos[1] - src_pos[1])**2 +
    (dst_pos[2] - src_pos[2])**2
  ) 
 
def g_to_ms2(accel_g):
  return accel_g * G_IN_MS2

def distance_point_to_segment(p, a, b):
  """Returns shortest distance from point p to segment a-b."""
  p, a, b = np.array(p), np.array(a), np.array(b)
  ab = b - a
  t = np.dot(p - a, ab) / np.dot(ab, ab)
  t = np.clip(t, 0, 1)
  projection = a + t * ab
  return np.linalg.norm(p - projection)
  
def move_towards(current, target, distance):
  current, target = np.array(current), np.array(target)
  direction = target - current
  length = np.linalg.norm(direction)
  if length == 0 or distance >= length:
      return tuple(target)
  return tuple(current + direction / length * distance)

def delta_v(isp, mass_ratio):
  return isp * G_IN_MS2 * np.log(mass_ratio)