import random

def get_weights(items, falloff=0.7):
  n = len(items)
  if n == 0:
    return []
  
  weights = [falloff ** i for i in range(n)]
  total = sum(weights)
  normalized = [w / total for w in weights]
  
  return normalized

def weighted_random(items, falloff=0.7):
  n = len(items)
  if n == 0:
    return []
  
  weights = [falloff ** i for i in range(n)]
  total = sum(weights)
  
  weights = [w / total for w in weights]
  
  return random.choices(items, weights=weights)[0]