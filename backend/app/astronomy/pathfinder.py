from .objects import AstronomicalBody, LagrangePointObject, Star, STAR, ALL_OBJECTS
from .vessels import Vessel
from .utils import distance_at_time, g_to_ms2, distance_point_to_segment, linear_distance

import math
import numpy as np
from typing import List, Tuple
import heapq

MAX_ACCEL_G = 0.8
AU_IN_METER = 1.496e11
  
class Policy:
  def __init__(
    self,
    time_weight=1.0,
    cost_weight=1.0,
    comfort_weight=1.0,
    disable_coast=False,
  ):
    self.time_weight = time_weight
    self.cost_weight = cost_weight
    self.comfort_weight = comfort_weight
    self.disable_coast = disable_coast
    
  def evaluate(self, profile: 'Profile'):
    if profile is None:
      return
    if self.disable_coast and profile.coast_time > 0:
      return float("inf")
    
    cost = (
      (self.time_weight * (profile.total_time / 1000)) +
      (self.cost_weight * profile.dv_cost / 1000) + 
      (self.comfort_weight * (MAX_ACCEL_G - profile.accel_g) * 1000) +
      (self.comfort_weight * profile.coast_time / 3600)
    )
    
    return cost
    
class NodeState:
  def __init__(self, position: AstronomicalBody, timestamp, dv_remaining, path_history):
    self.position = position
    self.timestamp = timestamp
    self.dv_remaining = dv_remaining
    self.path_history = path_history
    self.cost_so_far = 0.0
    self.heuristic = 0.0
    self.total_cost = 0.0
    
  def __lt__(self, other):
    return self.total_cost < other.total_cost
    
class Profile:
  def __init__(self, burn_time, coast_time, dv_cost, dv_to_refuel, accel_g, v_peak, distance_traveled):
    self.burn_time = burn_time
    self.coast_time = coast_time
    self.dv_cost = dv_cost
    self.dv_to_refuel = dv_to_refuel
    self.accel_g = accel_g
    self.v_peak = v_peak
    self.distance_traveled = distance_traveled
    
    self.total_time = burn_time + coast_time
    
    
class PathFinder:
  def __init__(self, vessel: Vessel, policy: Policy, nodes: List[AstronomicalBody] = ALL_OBJECTS.values()):
    self.vessel = vessel
    self.policy = policy
    self.nodes = nodes
    self.max_accel_g = min(MAX_ACCEL_G, self.vessel.max_acceleration())
    
    self.search_log = []
    self.launch_time = None
    self.origin: AstronomicalBody = None
    self.full_path: List[Tuple[Profile, AstronomicalBody]] = []
    
  def find_path(self, origin: AstronomicalBody, destination: AstronomicalBody, launch_time, mandatory_stops=None, strict_order=True):
    if destination not in self.nodes:
      return None
    
    self.launch_time = launch_time
    self.origin = origin

    if mandatory_stops is None:
      mandatory_stops = []
      strict_order = False
    
    if strict_order:
      waypoints = [origin] + mandatory_stops + [destination]
      return self.find_path_for_waypoints(waypoints, launch_time)
    
    start_state = NodeState(
      position=origin,
      timestamp=launch_time,
      dv_remaining=self.vessel.delta_v,
      path_history=[]
    )
    
    open_set = []
    heapq.heappush(open_set, (0, start_state))
    
    visited = set()
    best_cost = {}
    MAX_ITER = 500
    iterations = 0
    
    while open_set and iterations < MAX_ITER:
      iterations += 1
      current_cost, current_state = heapq.heappop(open_set)
      state_key = (current_state.position.name, round(current_state.timestamp))
      
      if state_key in visited:
        continue
      
      log_entry = f"Expanded {current_state.position.name} at time {current_state.timestamp:.1f}, cost_so_far {current_state.cost_so_far:.1f}"
      self.search_log.append(log_entry)
      
      if current_state.position == destination:
        self.full_path = current_state.path_history
        return current_state.path_history
      
      for neighbor in self.nodes:
        if neighbor == current_state.position:
          continue
        
        profiles = self.generate_candidate_profiles(current_state, neighbor)
        profiles = [p for p in profiles if p is not None]
        
        if not profiles:
          continue
        
        for profile in profiles:
          
          profile_cost = self.policy.evaluate(profile)
          
          arrival_time = current_state.timestamp + profile.total_time
          new_dv_remaining = current_state.dv_remaining - profile.dv_cost
          
          if new_dv_remaining < 0:
            new_dv_remaining = self.vessel.delta_v
            
          new_path_history = list(current_state.path_history)
          new_path_history.append((profile, neighbor))
          
          next_state = NodeState(
            position=neighbor,
            timestamp=arrival_time,
            dv_remaining=new_dv_remaining,
            path_history=new_path_history
          )
          
          next_state.cost_so_far = current_state.cost_so_far + profile_cost
          next_state.heuristic = self.estimate_heuristic(next_state, destination)
          next_state.total_cost = next_state.cost_so_far + next_state.heuristic
          
          next_key = (neighbor.name, round(arrival_time))
          if next_key in best_cost and next_state.total_cost >= best_cost[next_key]:
            continue
          best_cost[next_key] = next_state.total_cost
          
          heapq.heappush(open_set, (next_state.total_cost, next_state))
        
    return None

  def find_path_for_waypoints(self, waypoints: List[AstronomicalBody], launch_time):
    full_path = []
    current_origin = waypoints[0]
    current_time = launch_time
    
    for next_target in waypoints[1:]:
      leg_path = self.find_path(current_origin, next_target, current_time)
      if not leg_path:
        full_path = None
      full_path.extend(leg_path)
      current_origin = next_target
      current_time += sum(profile.total_time for profile, _ in leg_path)

    self.full_path = full_path
    self.origin = waypoints[0]
    return full_path
        
  def generate_candidate_profiles(self, state: NodeState, target: AstronomicalBody):
    profiles = []
    
    timestamp = state.timestamp
    origin = state.position
    distance_to_target, arrival_time = self.estimate_arrival(origin, target, timestamp)
    
    if not self.validate_path(origin, target, timestamp, arrival_time):
      return profiles
    
    dv_remaining = state.dv_remaining
    max_dv = self.vessel.delta_v
  
    # Try make the trip without refueling
    profiles.append(self.compute_travel_time(distance_to_target, self.max_accel_g, max_dv=dv_remaining))
    
    # Assuming refueling
    profiles.append(self.compute_travel_time(distance_to_target, self.max_accel_g, force_no_coast=True, force_accel=True))
    profiles.append(self.compute_travel_time(distance_to_target, self.max_accel_g, force_no_coast=True))
    profiles.append(self.compute_travel_time(distance_to_target, self.max_accel_g))
      
    profiles.append(self.compute_travel_time(distance_to_target, self.max_accel_g, max_dv=0.9 * max_dv))
    profiles.append(self.compute_travel_time(distance_to_target, self.max_accel_g, max_dv=0.8 * max_dv))
    profiles.append(self.compute_travel_time(distance_to_target, self.max_accel_g, max_dv=0.7 * max_dv))
    profiles.append(self.compute_travel_time(distance_to_target, self.max_accel_g, max_dv=0.6 * max_dv))
    profiles.append(self.compute_travel_time(distance_to_target, self.max_accel_g, max_dv=0.5 * max_dv))
    
    profiles.append(self.compute_travel_time(distance_to_target, self.max_accel_g * 0.9))
    profiles.append(self.compute_travel_time(distance_to_target, self.max_accel_g * 0.8))
    profiles.append(self.compute_travel_time(distance_to_target, self.max_accel_g * 0.7))
    profiles.append(self.compute_travel_time(distance_to_target, self.max_accel_g * 0.6))
    profiles.append(self.compute_travel_time(distance_to_target, self.max_accel_g * 0.5))
    
    return profiles
  
  def estimate_arrival(self, origin: AstronomicalBody, target: AstronomicalBody, timestamp):
    static_distance = distance_at_time(origin, target, timestamp)
    fast_profile = self.compute_travel_time(static_distance, self.max_accel_g)
    slow_profile = self.compute_travel_time(static_distance, 0.05, max_dv=0.3*self.vessel.delta_v)
    average_travel_time = np.average([fast_profile.total_time, slow_profile.total_time])
    
    arrival_time = timestamp + average_travel_time
    new_target_pos = target.position_at_time(arrival_time)
    new_distance = linear_distance(origin.position_at_time(timestamp), new_target_pos) * AU_IN_METER
    
    return new_distance, arrival_time
    
  def estimate_heuristic(self, state: NodeState, destination: AstronomicalBody):
    current_node = state.position
    direct_distance = distance_at_time(current_node, destination, state.timestamp)
    pseudo_profile = self.compute_travel_time(direct_distance, self.max_accel_g) 
    
    if pseudo_profile is None:
      return 0.0
    
    return self.policy.evaluate(pseudo_profile)
  
  def validate_path(self, origin: AstronomicalBody, target: AstronomicalBody, departure_time, arrival_time):
    valid = True
    
    midpoint_time = (departure_time + arrival_time) / 2
    
    all_objects = list(ALL_OBJECTS.values())
    all_objects.append(STAR)
    
    origin_pos = origin.position_at_time(departure_time)
    target_pos = target.position_at_time(arrival_time)
    
    for body in all_objects:
      if isinstance(body, LagrangePointObject):
        continue
      
      if body in (origin, target):
        continue
    
      body_pos = body.position_at_time(midpoint_time)
      min_distance = distance_point_to_segment(body_pos, origin_pos, target_pos) * AU_IN_METER
      
      safe_distance = body.safe_range()
      if safe_distance is None:
        continue
      if min_distance < safe_distance:
        valid = False
        break
    return valid
        
  def compute_travel_time(self, distance_m, accel_g, force_no_coast=False, force_accel=False, max_dv=None, step=0.01):
    if max_dv is None:
      max_dv = self.vessel.delta_v
      
    while accel_g >= step:
      # loops acceleration until minimum allowed
      try:
        max_distance = self.vessel.max_distance_at(accel_g, max_dv)
        distance_to_coast = max(0, distance_m - max_distance)
        distance_to_accel = distance_m - distance_to_coast
        need_coasting = distance_to_coast > 0
      
        if distance_to_accel <= 0:
          # max_distance is way too small
          break
        
        accel_time = math.sqrt((2 * (distance_to_accel / 2)) / g_to_ms2(accel_g))
        v_peak = g_to_ms2(accel_g) * accel_time
        dv_cost = v_peak * 2
        dv_to_refuel = max_dv - dv_cost
        burn_time = 2 * accel_time
      
        if need_coasting:
          if force_no_coast:
            # force no coasting, try lower acceleration
            if force_accel or accel_g <= step:
              # can't lower acceleration or acceleration too small
              break
            accel_g -= step
            # lower and recompute
            continue
          # calculate coast time
          coast_time = distance_to_coast / v_peak
          return Profile(burn_time, coast_time, dv_cost, dv_to_refuel, accel_g, v_peak, distance_m)
        else:
          # no coasting
          coast_time = 0.0
          return Profile(burn_time, coast_time, dv_cost, dv_to_refuel, accel_g, v_peak, distance_m)
      
      except Exception as e:
        print(f"Failed to calculate path: {e}")
        break
      
    return None
  
  def print_search_log(self):
    print("\n=== Search Log ===")
    for entry in self.search_log:
        print(entry)
        
  def save_search_log(self, filename="./data/search_log.txt"):
    try:
      with open(filename, 'w', encoding='utf-8') as f:
        for log in self.search_log:
          f.write(f"{log}\n")
        f.close()
    except Exception as e:
      print(f"Failed to save search log: {e}")
  
  def display_path(self):
    if not self.full_path:
      print("No path found.")
      return
    
    print("\n===== Full Path =====")
    for idx, (profile, body) in enumerate(self.full_path, 1):
      print(f"\nLeg {idx}: {body.name} ({profile.distance_traveled / 1.496e11:.2f} AU)")
      print(f"Total Time: {profile.burn_time / 3600:.1f} + {profile.coast_time / 3600:.1f} hours / {profile.total_time / 86400:.2f} days total")
      print(f"Delta-V Cost: {profile.dv_cost / 1000:.1f} km/s")
      print(f"Acceleration: {profile.accel_g:.2f} g")
      
  def parse_path(self):
    if not self.full_path:
      return {"error": "No path found"}
    
    legs = []
    total_time = 0.0
    total_distance = 0.0
    total_cost = 0.0
    total_accel = 0.0
    
    for idx, (profile, body) in enumerate(self.full_path, 1):
      leg_info = {
          "leg_number": idx,
          "destination": body.name,
          "distance_au": profile.distance_traveled / 1.496e11,
          "burn_time": profile.burn_time,
          "coast_time": profile.coast_time,
          "total_time": profile.total_time,
          "dv_cost": profile.dv_cost,
          "accel_g": profile.accel_g,
      }
      legs.append(leg_info)

      total_time += profile.total_time
      total_distance += profile.distance_traveled
      total_cost += profile.dv_cost
      total_accel += profile.accel_g

    summary = {
      "total_legs": len(legs),
      "total_time_days": total_time / 86400,
      "total_distance_au": total_distance / 1.496e11,
      "total_delta_v_km_s": total_cost / 1000,
      "average_acceleration_g": total_accel / len(legs),
    }

    return {
      "origin": self.origin.name,
      "launch_time": self.launch_time,
      "legs": legs,
      "summary": summary
    }