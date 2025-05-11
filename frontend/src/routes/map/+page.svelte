<script lang="ts">
  import Clock from "$lib/components/Clock.svelte";
  import Map from "$lib/components/Map.svelte";
  import { setSystemState } from "$lib/system.svelte";

  setSystemState();
</script>

<Clock showAsOverlay={true} font="Consolas"></Clock>
<Map fullScreen={true}></Map>