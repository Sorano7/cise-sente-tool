from enum import Enum
import random
from .phonology import CONSONANTS, VOWELS, CODAS
from .utils import weighted_random, get_weights

class WordType(Enum):
  NOUN = 1
  VERB = 2
  ADJECTIVE = 3

class WordGenerator:
  def __init__(self):
    pass
  
  def generate(self, type: WordType=None, syllable_count=0):
    syllables = []
    
    if syllable_count == 0:
      syllable_count = random.choice(range(7))

    for _ in range(syllable_count - 1):
      syllables.append(self.generate_syllable())
      
    if type is None:
      type = random.choice(list(WordType))
      
    match type:
      case WordType.NOUN:
        syllables.append(self.generate_syllable(not_endswith=['us', 'ar']))
      case WordType.VERB:
        syllables.append(self.generate_syllable(endswith=['us', 'ar']))
      case WordType.ADJECTIVE:
        syllables.append(self.generate_syllable(endswith=['ui', 'ki']))
      
    return "'".join(syllables)

  def generate_syllable(self, endswith=[], not_endswith=[]):
    consonants = list(CONSONANTS.keys())
    consonants.insert(5, "")
    vowels = list(VOWELS.keys())
    codas = ["", *list(CODAS.keys())]

    
    onset = weighted_random(consonants, falloff=1)
    vowel = weighted_random(vowels, falloff=0.5)
    coda = weighted_random(codas, falloff=0.6)

    if onset == 'w' and vowel == 'u':
      onset = ''
    
    if onset == 'y' and vowel == 'i':
      onset = ''
      
    end = vowel + coda
    
    if not endswith:
      while end in not_endswith:
        vowel = weighted_random(vowels)
        coda = weighted_random(codas)
        end = vowel + coda
    else:
      while end in not_endswith or end not in endswith:
        end = random.choice(endswith)     
       
    return onset + end
    
  