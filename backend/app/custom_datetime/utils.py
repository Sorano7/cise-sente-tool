def count_cycle(cycle, target, seconds_per_day):
    """Return number of full cycles in target"""
    
    value = 0
    elapsed = 0
    for pos, item in enumerate(cycle):
      elapsed += item * seconds_per_day
      if elapsed >= target:
        value = pos + 1
        break
    return value