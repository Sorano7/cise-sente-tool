import re
from enum import Enum
from typing import List
import random
from .phonology import CONSONANTS, VOWELS, CODAS, COMPOSITES
from .utils import weighted_random

class WordType(Enum):
  NOUN = 1
  VERB = 2
  ADJECTIVE = 3
  
class Syllable:
  onsets = ["", *list(CONSONANTS.keys()), *list(COMPOSITES.keys())]
  vowels = list(VOWELS.keys())
  codas = ["", *list(CODAS.keys())]
    
  def __init__(self, onset: str, vowel: str, coda: str):
    self.onset = onset
    self.vowel = vowel
    self.coda = coda
    
  @classmethod
  def random(cls, not_endswith=[], endswith=[]):
    onset = weighted_random(cls.onsets, falloff=1)
    vowel = weighted_random(cls.vowels, falloff=0.5)
    coda = weighted_random(cls.codas, falloff=0.4)
    
    if onset.strip():
      if onset == 'w' and vowel == 'u':
        onset = ''
      
      if onset[-1] == 'y' and vowel == 'i':
        onset = ''
    
    if not_endswith:
      if sorted(not_endswith) == sorted(endswith):
        raise ValueError("not_endswith cannot match endswith")
      while vowel + coda in not_endswith:
        if endswith:
          vowel, coda = random.choice(endswith)
        else:
          vowel = weighted_random(cls.vowels, falloff=0.5)
          coda = weighted_random(cls.codas, falloff=0.4)
          
    elif endswith:
      vowel, coda = random.choice(endswith)
    
    return cls(onset, vowel, coda)
  
  @classmethod
  def word_ending(cls, type: WordType):
    match type:
      case WordType.NOUN:
        return cls.random(not_endswith=['ar', 'us', 'ui', 'ki'])
      case WordType.VERB:
        return cls.random(endswith=['ar', 'us'])
      case WordType.ADJECTIVE:
        if random.random() < 0.5:
          return cls('k', 'i', '')
        else:
          return cls.random(endswith=['ui'])
        
  @classmethod
  def from_string(cls, str: str):
    if not str.strip():
      raise ValueError("String cannot be empty")
    
    onset = ''
    vowel = ''
    coda = ''
    
    while str:
      char = str[-1]
      
      if char in CODAS:
        coda = char
      elif char in VOWELS:
        vowel = char
        
      str = str[:-1]
      
      if vowel.strip():
        break
      
    onset = str
    
    return cls(onset, vowel, coda)
        
  def __str__(self):
    return self.onset + self.vowel + self.coda
  
  def has_coda(self):
    if self.coda.strip():
      return True
    return False
  
  def has_onset(self):
    if self.onset.strip():
      return True
    return False
  
  def startswith_coda(self):
    if not self.onset.strip():
      return False
    return self.onset[0] in CODAS
  
  def is_composite_onset(self):
    return self.onset in COMPOSITES

class WordGenerator:
  def __init__(self):
    pass
  
  def generate(self, type: WordType=None, syllable_count=0):
    syllables = []
    
    if syllable_count == 0:
      syllable_count = random.choice(range(7))

    for _ in range(syllable_count - 1):
      syllables.append(Syllable.random())
      
    if type is None:
      type = random.choice(list(WordType))
      
    syllables.append(Syllable.word_ending(type))
    word = self.parse_syllables(syllables)
      
    return word
  
  def parse_syllables(self, syllables: List[Syllable]):
    current_syll = syllables[0]
    result = str(current_syll)
    
    for i in range(1, len(syllables)):
      prev = current_syll
      next_ = syllables[i]
      
      if prev.has_coda() and not next_.has_onset():
        result += "'"
        
      elif not prev.has_coda() and next_.startswith_coda() and next_.is_composite_onset():
        result += "'"
      
      current_syll = next_
      result += str(current_syll)
      
    return result