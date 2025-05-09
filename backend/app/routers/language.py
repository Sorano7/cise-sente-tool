from fastapi import APIRouter, HTTPException
from ..language.word_generator import WordType, WordGenerator
from typing import Optional

router = APIRouter()

@router.get("/word")
def get_new_word(type: Optional[str]=None, syllable_count: Optional[int]=0):
  word_type_str = type.strip().upper()
  if WordType[word_type_str]:
    word_type = WordType[word_type_str]
    
  if not word_type:
    raise HTTPException("Invalid word type")
  
  wg = WordGenerator()
  word = wg.generate(word_type, syllable_count)
  
  return { "word": word }
    
  
    
  