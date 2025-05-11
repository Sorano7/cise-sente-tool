<script lang="ts">
  import { onMount } from "svelte";
  import { getSystemState } from "$lib/system.svelte";

  const systemState = getSystemState();

  let selectedPreset = $state("");
  let launchTimeInput = $state(systemState.timestamp.toFixed(0).toString());

  onMount(async () => {
    systemState.updateVesselPresets();
  });

  function applyVesselPreset() {
    if (selectedPreset) {
      systemState.applyVesselPreset(selectedPreset);
    }
  }

  function showTransitMenu() {
    systemState.showContextMenu = true;
  }

  async function applyLaunchTime() {
    await systemState.applyTimeString(launchTimeInput);
    if (launchTimeInput === "") launchTimeInput = systemState.timestamp.toFixed(0).toString();
  }

  function focusOnPlanet() {
    systemState.focusOnObject = true;
  }
</script>

<div class="controls-container">
  <div class="card-row">
    <!-- Vessel Block -->
    <div class="option-card">
      <h4>Vessel Specs</h4>

      <div class="form-group">
        <label for="preset">Preset</label>
        <select
          id="preset"
          bind:value={selectedPreset}
          onchange={applyVesselPreset}
        >
          <option value="">Custom</option>
          {#each Object.keys(systemState.vesselPresets) as preset}
            <option value={preset}>{preset}</option>
          {/each}
        </select>
      </div>

      <div class="form-group">
        <label for="delta-v">Delta-V (m/s)</label>
        <input id="delta-v" type="number" bind:value={systemState.vesselConfig.deltaV} min="0" />
      </div>

      <div class="form-group">
        <label for="mass">Mass (t)</label>
        <input id="mass" type="number" bind:value={systemState.vesselConfig.massT} min="0" />
      </div>

      <div class="form-group">
        <label for="thrust">Thrust (N)</label>
        <input id="thrust" type="number" bind:value={systemState.vesselConfig.thrustN} min="0" />
      </div>
    </div>

    <!-- Policy Block -->
    <div class="option-card">
      <h4>Search Policy</h4>

      <div class="form-group">
        <label for="time-weight">Time Weight</label>
        <input
          id="time-weight"
          type="range"
          min="0"
          max="5"
          bind:value={systemState.policy.timeWeight}
          step="0.1"
        />
      </div>

      <div class="form-group">
        <label for="cost-weight">Cost Weight</label>
        <input
          id="cost-weight"
          type="range"
          min="0"
          max="5"
          bind:value={systemState.policy.costWeight}
          step="0.1"
        />
      </div>

      <div class="form-group">
        <label for="comfort-weight">Comfort Weight</label>
        <input
          id="comfort-weight"
          type="range"
          min="0"
          max="5"
          bind:value={systemState.policy.comfortWeight}
          step="0.1"
        />
      </div>

      <div class="form-group">
        <label
          ><input type="checkbox" bind:checked={systemState.policy.disableCoast} /> Disable Coasting</label
        >
      </div>
    </div>

    <!-- Object tools -->
    <div class="option-card">
      <h4>Object Tools</h4>

      <div class="form-group">
        <label for="selected-object">Select Object</label>
        <select id="selected-object" bind:value={systemState.selectedObject}>
          <option value="">Select...</option>
          {#each Object.keys(systemState.allObjects) as planet}
            <option value={planet}>{planet}</option>
          {/each}
        </select>
      </div>

      <div class="form-group button-group">
        <button onclick={showTransitMenu} disabled={!systemState.selectedObject}
          >Transit Setting</button
        >
        <button onclick={focusOnPlanet} disabled={!systemState.selectedObject}
          >Focus On Object</button
        >
      </div>
    </div>

    <!-- Settings block -->
    <div class="option-card">
      <h4>Settings</h4>
      <div class="form-group">
        <label for="launch-time">Time</label>
        <input id="launch-time" type="string" bind:value={launchTimeInput} />
        <button class="form-button" onclick={applyLaunchTime}>Apply</button>
      </div>

      <div class="form-group">
        <label for="launch-time">Transit</label>
        <button onclick={() => systemState.calculatePath()}>Calculate</button>
        <button onclick={() => systemState.clearPath()}>Clear</button>
      </div>
    </div>
  </div>
</div>

<style>
  .controls-container {
    flex: 0 0 auto;
    padding: 10px;
    background-color: #111;
    color: white;
  }

  .card-row {
    display: flex;
    gap: 20px;
    justify-content: space-between;
  }

  .option-card {
    flex: 1;
    min-width: 200px;
    background-color: #222;
    padding: 12px;
    border-radius: 6px;
    box-shadow: 0 0 4px rgba(255, 255, 255, 0.1);
  }

  .option-card h4 {
    margin-top: 0;
    margin-bottom: 10px;
    font-size: 1rem;
    border-bottom: 1px solid #444;
    padding-bottom: 4px;
  }

  .form-group {
    display: flex;
    flex-direction: column;
    margin-bottom: 10px;
    gap: 4px;
  }

  .button-group {
    display: flex;
    gap: 8px;
  }

  .button-group button {
    flex: 1;
    min-width: 0;
    white-space: nowrap;
    padding: 6px 4px;
  }

  button:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }
</style>
