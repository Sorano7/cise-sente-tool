<script lang='ts'>
  import WordGenerator from "$lib/components/WordGenerator.svelte";
</script>

<div class="container">
  <h1>Ina'ryorto</h1>
  <div class="word-panel">
    <WordGenerator></WordGenerator>
  </div>
</div>

<style>
  .container {
    display: flex;
    height: 100%;
    width: 100%;
    flex-direction: column;
    padding: 2rem;
  }
</style>

