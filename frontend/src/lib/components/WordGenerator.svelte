<script lang="ts">
  import { getNewWord, WordType } from "$lib/language.svelte";
    import { onMount } from "svelte";

  let wordType = $state("noun");
  let syllableCount = $state(0);
  let currentWord = $state("");

  onMount(async () => {
    currentWord = await getNewWord(wordType, syllableCount);
  });
</script>

<div class="container">
  <div class="word-label">{currentWord}</div>

  <div class="control-row">
    <div class="control-item">
      <label for="word-type">Type</label>
      <select id="word-type" bind:value={wordType}>
        {#each Object.keys(WordType) as type}
          <option value={type}>{type}</option>
        {/each}
      </select>
    </div>

    <div class="control-item">
      <label for="syllable-count">Syllable Count</label>
      <input id="syllable-count" bind:value={syllableCount} />
    </div>
  </div>

  <button
    onclick={async () => {
      currentWord = await getNewWord(wordType, syllableCount);
    }}
  >
    New
  </button>
</div>

<style>
  .container {
    max-width: 400px;
    margin: 40px auto;
    padding: 20px;
    border-radius: 8px;
    background-color: #222;
    box-shadow: 0 4px 10px rgba(0, 0, 0, 0.1);
    font-family: sans-serif;
  }

  .word-label {
    font-size: 32px;
    font-weight: 600;
    text-align: center;
    margin-bottom: 20px;
  }

  .control-row {
    display: flex;
    flex-direction: column;
    gap: 16px;
    margin-bottom: 20px;
  }

  .control-item {
    display: flex;
    flex-direction: column;
  }

  .control-item label {
    font-size: 14px;
    margin-bottom: 4px;
  }

  .control-item select,
  .control-item input {
    padding: 8px;
    border-radius: 4px;
    border: 1px solid #ccc;
    font-size: 14px;
  }

  button {
    width: 100%;
    padding: 10px;
    font-size: 16px;
    color: #111;
    border: none;
    border-radius: 4px;
    cursor: pointer;
  }
</style>
