<script lang="ts">
  import { onMount } from "svelte";
  import { getSystemState } from "$lib/system.svelte";
  import { API_CLOCK, loadData } from "$lib/api.svelte";

  const systemState = getSystemState();

  let { showAsOverlay = false, font = 'Space Mono' } = $props();

  const SYNC_INTERVAL = 300000;

  interface CalendarDisplay {
    segments: number[];
    separators: string[];
    rules: (number | null)[];
    digits: number[];
  }

  interface ClockResponse {
    timestamp: number;
    meaji: CalendarDisplay;
    imor: CalendarDisplay;
    junesgi: CalendarDisplay;
    earth: string;
  }

  let earthTime = $derived.by(() => {
    return formatEarthDate(new Date(systemState.getUnixTimestamp() * 1000));
  });
  let meaji: CalendarDisplay | null = $state(null);
  let imor: CalendarDisplay | null = $state(null);
  let junesgi: CalendarDisplay | null = $state(null);

  onMount(() => {
    syncClock();
    const tick = setInterval(tickClock, 1000);
    const sync = setInterval(() => syncClock(), SYNC_INTERVAL);

    return () => {
      clearInterval(tick);
      clearInterval(sync);
    };
  });

  /**
   * Format Earth date in yyyy.MM.dd, hh.mm.ss
   *
   * @param {Date} earthDate Date object to process
   */
  function formatEarthDate(earthDate: Date) {
    const yyyy = earthDate.getUTCFullYear();
    const mm = String(earthDate.getUTCMonth() + 1).padStart(2, "0");
    const dd = String(earthDate.getUTCDate()).padStart(2, "0");
    const hh = String(earthDate.getUTCHours()).padStart(2, "0");
    const min = String(earthDate.getUTCMinutes()).padStart(2, "0");
    const ss = String(earthDate.getUTCSeconds()).padStart(2, "0");

    return `${yyyy}.${mm}.${dd}, ${hh}:${min}:${ss}`;
  }

  /**
   * Sync clock with API
   */
  async function syncClock() {
    const data: ClockResponse = await loadData(`${API_CLOCK}/init`);

    systemState.timestamp = Math.round(data.timestamp);
    meaji = data.meaji;
    imor = data.imor;
    junesgi = data.junesgi;

    console.log(
      `[Clock] Synced. Next sync at ${new Date(Date.now() + SYNC_INTERVAL)}`,
    );
  }

  /**
   * Increment current time by 1. Request sync if unable to increment.
   */
  function tickClock() {
    if (!meaji || !imor || !junesgi) return;

    systemState.timestamp += 1;
    if (!incrementCalendar(meaji)) syncClock();
    if (!incrementCalendar(imor)) syncClock();
    if (!incrementCalendar(junesgi)) syncClock();
  }

  /**
   * Increment calendar by 1 second based on provided rules and return success status
   *
   * @param {CalendarDisplay} cd CalendarDisplay object to process
   * @returns {boolean} whether the incrementation succeeded or not
   */
  function incrementCalendar(cd: CalendarDisplay): boolean {
    for (let i = cd.rules.length - 1; i >= 0; i--) {
      if (cd.rules[i] == null) return false;

      cd.segments[i]++;
      if (cd.segments[i] >= cd.rules[i]!) {
        cd.segments[i] = 0;
      } else {
        break;
      }
    }
    return true;
  }

  /**
   * Pad the start of a number with 0 based on target length
   *
   * @param num Number to process
   * @param length Target length
   */
  function pad(num: number, length: number) {
    return length > 0 ? num.toString().padStart(length, "0") : num.toString();
  }

  /**
   * Format a generic calendar with no special rules
   *
   * @param cd CalendarDisplay object to process
   */
  function formatGeneric(cd: CalendarDisplay): string {
    return cd.segments
      .map((val, i) => {
        const padded = pad(val, cd.digits[i] ?? 0);
        return padded + (cd.separators[i] || "");
      })
      .join("");
  }

  const QUARTER_NAMES = ["Fu", "Se", "Myu", "Jo"];

  /**
   * Format Meaji calendar with Quarter-Hour format
   *
   * @param cd
   */
  function formatMeaji(cd: CalendarDisplay): string {
    const hour = cd.segments[4];
    const relHour = hour % 8;
    const quarterIndex = Math.floor(hour / 8);
    const quarter = QUARTER_NAMES[quarterIndex];

    return cd.segments
      .map((val, i) => {
        let padded = pad(val, cd.digits[i] ?? 0);
        if (i === 3) padded = quarter;
        if (i === 4) padded = relHour.toString();
        return padded + (cd.separators[i] || "");
      })
      .join("");
  }
</script>

<div class={`clock-container ${showAsOverlay ? 'overlay' : ''}`} style={`font-family: ${font};`}>
  {#if meaji && imor && junesgi}
    <div class="clock-group">
      <div class="clock-label">Timestamp</div>
      <div class="clock-value">{systemState.timestamp}</div>
    </div>
    <div class="clock-group">
      <div class="clock-label">Meaji</div>
      <div class="clock-value">{formatMeaji(meaji)}</div>
    </div>
    <div class="clock-group">
      <div class="clock-label">Imor</div>
      <div class="clock-value">{formatGeneric(imor)}</div>
    </div>
    <div class="clock-group">
      <div class="clock-label">Junesgi</div>
      <div class="clock-value">{formatGeneric(junesgi)}</div>
    </div>
    <div class="clock-group">
      <div class="clock-label">Earth (UTC)</div>
      <div class="clock-value">{earthTime}</div>
    </div>
  {/if}
</div>

<style>
  .clock-container {
    display: flex;
    flex-wrap: wrap;
    gap: 1.2rem;
    justify-content: center;
  }

  .overlay {
    position: fixed;
    top: 0;
    left: 0;
    margin: 1em;
  }

  .clock-group {
    margin-bottom: 1.2rem;
  }

  .clock-label {
    font-size: 0.85rem;
    color: #888;
    margin-bottom: 0.25rem;
  }

  .clock-value {
    font-size: 1rem;
    font-weight: 500;
    color: #fff;
    white-space: nowrap;
  }
  @media (min-width: 1500px) {
    .clock-container {
      flex-direction: column;
    }
  }
</style>
