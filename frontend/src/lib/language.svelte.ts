import { API_LANGUAGE, loadData } from "./api.svelte";

export enum WordType {
  NOUN = 'noun',
  VERB = 'verb',
  ADJECTIVE = 'adjective'
}

export async function getNewWord(type: string, syllableCount: number) {
  const params = new URLSearchParams({ type: type, syllable_count: syllableCount.toString() })
  const data = await loadData(`${API_LANGUAGE}/word?${params}`);
  return data.word
}