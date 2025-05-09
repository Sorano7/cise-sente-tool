<script lang="ts">
  import { setSystemState } from "$lib/system.svelte";
  import Clock from "$lib/components/Clock.svelte";
  import Map from "$lib/components/Map.svelte";
  import TransitDetail from "$lib/components/TransitDetail.svelte";
  import TransitOptions from "$lib/components/TransitOptions.svelte";

  setSystemState();
</script>

<div class="page-layout">
  <!-- System Clock Panel -->
  <div class="clock-panel">
    <h3>System Clock</h3>
    <Clock font="Consolas"></Clock>
  </div>

  <!-- Map & Transit -->
  <div class="main-container">
    <!-- Canvas & Transit Controls -->
    <div class="left-panel">
      <Map></Map>
      <TransitOptions></TransitOptions>
    </div>

    <!-- Transit Details -->
    <div class="right-panel">
      <TransitDetail></TransitDetail>
    </div>
  </div>
</div>

<style>
  .page-layout {
    display: flex;
    flex-direction: column;
    height: 100vh;
    width: 100vw;
    overflow: hidden;
    font-family: "Inter";
  }

  .main-container {
    flex: 1;
    display: flex;
    width: 100%;
  }

  .left-panel {
    display: flex;
    flex-direction: column;
    background-color: black;
    height: 100vh;
  }

  .right-panel {
    flex: 1;
    padding: 10px;
    background-color: #1a1a1a;
    color: white;
    display: flex;
    flex-direction: column;
  }

  /* Wide Layout */
  @media (min-width: 1500px) {
    .page-layout {
      flex-direction: row;
    }

    .clock-panel {
      height: 100vh;
      flex-shrink: 0;
    }
  }

  .clock-panel {
    padding: 1rem;
    background: #111;
    color: #eee;
    font-family: "Inter";
    border-right: 1px solid #333;
    min-width: 200px;
    box-sizing: border-box;
    padding: 10px;
    min-height: 15vh;
    border-bottom: 2px solid #333;
  }
</style>
