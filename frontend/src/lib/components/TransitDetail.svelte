<script lang="ts">
  import { getSystemState } from "./System.svelte";

  const systemState = getSystemState();
</script>

<div class="trip-summary">
  <h3>Transit Summary</h3>
  {#if systemState.pathResult?.summary}
    <div class="trip-summary-row">
      <span class="label">Distance</span>
      <span class="divider">—</span>
      <span
        ><span class="value"
          >{systemState.pathResult.summary.total_distance_au.toFixed(2)}</span
        > <span class="unit">AU</span></span
      >
    </div>
    <div class="trip-summary-row">
      <span class="label">Travel Time</span>
      <span class="divider">—</span>
      <span
        ><span class="value"
          >{systemState.pathResult.summary.total_time_days.toFixed(2)}</span
        > <span class="unit">d</span></span
      >
    </div>
    <div class="trip-summary-row">
      <span class="label">Delta-V Cost</span>
      <span class="divider">—</span>
      <span
        ><span class="value"
          >{systemState.pathResult.summary.total_delta_v_km_s.toFixed(1)}</span
        > <span class="unit">km/s</span></span
      >
    </div>
    <div class="trip-summary-row">
      <span class="label">Avg. Acceleration</span>
      <span class="divider">—</span>
      <span
        ><span class="value"
          >{systemState.pathResult.summary.average_acceleration_g.toFixed(2)}</span
        > <span class="unit">g</span></span
      >
    </div>
  {:else}
    <div>No transit data.</div>
  {/if}
</div>

<div class="trip-flow">
  <h4>Transit Flow</h4>
  {#if systemState.pathResult?.legs}
    <div class="trip-card">
      <div class="trip-card-header">
        <div class="leg-index-name">
          <div class="leg-title">
            0: {systemState.pathResult.origin}
          </div>
          <div class="leg-distance">Launch</div>
        </div>
        <div class="vertical-divider"></div>
        <div class="leg-details">
          <div class="leg-detail-row">
            <span class="label">t₀</span>
            <span class="divider">—</span>
            <span class="value">{systemState.path.launchTimeUnix.toFixed(0)}</span>
          </div>
        </div>
      </div>
    </div>

    {#each systemState.pathResult.legs as leg, index}
      <div class="trip-card">
        <div class="trip-card-header">
          <div class="leg-index-name">
            <div class="leg-title">
              {index + 1}: {leg.destination}
            </div>
            <div class="leg-distance">
              {leg.distance_au.toFixed(2) === "0.01"
                ? `${(leg.distance_au * 1.496e8).toFixed(2)}  km`
                : `${leg.distance_au.toFixed(2)} AU`}
            </div>
          </div>

          <div class="vertical-divider"></div>

          <div class="leg-details">
            <div class="leg-details">
              <div class="leg-detail-row">
                <span class="label">t</span>
                <span class="divider">—</span>
                <span>
                  <span class="value">{(leg.burn_time / 3600).toFixed(1)}</span>
                  <span class="unit">+</span>
                  <span class="value">{(leg.coast_time / 3600).toFixed(1)}</span
                  > <span class="unit">hrs</span>
                  (<span class="value"
                    >{(leg.total_time / 86400).toFixed(2)}</span
                  > <span class="unit">d</span>)
                </span>
              </div>
              <div class="leg-detail-row">
                <span class="label">a</span>
                <span class="divider">—</span>
                <span
                  ><span class="value">{leg.accel_g.toFixed(2)}</span>
                  <span class="unit">g</span></span
                >
              </div>
              <div class="leg-detail-row">
                <span class="label">Δv</span>
                <span class="divider">—</span>
                <span
                  ><span class="value">{(leg.dv_cost / 1000).toFixed(1)}</span>
                  <span class="unit">km/s</span></span
                >
              </div>
            </div>
          </div>
        </div>
      </div>
    {/each}
  {:else}
    <div>No transit data.</div>
  {/if}
</div>

<style>
  .trip-summary {
    margin-bottom: 20px;
  }

  .trip-flow {
    flex: 1;
    overflow-y: auto;
    border-top: 2px solid #333;
    padding-top: 10px;
  }

  .trip-card {
    background-color: #222;
    padding: 10px;
    border-radius: 6px;
    margin-bottom: 10px;
    display: flex;
    flex-direction: column;
  }

  .trip-card-header {
    display: flex;
    align-items: center;
    gap: 10px;
  }

  .leg-index-name {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    min-width: 80px;
    text-align: center;
  }

  .leg-title {
    font-weight: bold;
    font-size: 1rem;
  }

  .leg-distance {
    font-size: 0.8rem;
    color: #aaa;
  }

  .vertical-divider {
    width: 2px;
    height: 60px;
    background-color: #444;
  }

  .leg-details {
    display: flex;
    flex-direction: column;
    gap: 4px;
    font-size: 0.9rem;
  }

  .value {
    font-weight: 500;
    font-size: 1.1em;
  }

  .unit {
    font-size: 0.85em;
    color: #aaa;
  }

  .trip-summary-row {
    display: flex;
    align-items: baseline;
    margin-bottom: 4px;
    gap: 0.5rem;
    width: 100%;
  }

  .label {
    min-width: 8.5rem;
    text-align: left;
    color: #ccc;
    font-weight: 400;
  }

  .divider {
    color: #666;
    width: 1ch;
    text-align: center;
    margin-right: 4px;
  }

  .leg-details {
    margin-top: 0.4rem;
  }

  .leg-detail-row {
    display: inline-flex;
    align-items: baseline;
    margin-bottom: 2px;
    gap: 0.4rem;
  }

  .leg-detail-row .label {
    min-width: 1.2rem;
    text-align: left;
    color: #ccc;
    font-weight: 400;
  }

  .leg-detail-row .divider {
    width: 0.75rem;
    text-align: center;
    color: #666;
  }

  .leg-detail-row .value {
    font-weight: 500;
  }

  .leg-detail-row .unit {
    font-size: 0.85em;
    color: #aaa;
    margin-left: 3px;
  }
</style>
