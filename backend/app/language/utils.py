import random

def weighted_random(items, falloff=0.7):
  n = len(items)
  if n == 0:
    return []
  
  weights = [falloff ** i for i in range(n)]
  total = sum(weights)
  
  weights = [w / total for w in weights]
  
  return random.choices(items, weights=weights)[0]