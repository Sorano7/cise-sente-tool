<script lang="ts">
    import Nav from '$lib/components/Nav.svelte';

  let { children } = $props();

  let mouseY = $state(0);

  let showNav = $derived.by(() => {
    if (mouseY < 60) {
      return true;
    }
    return false;
  });

  function handleMouseMove(e: MouseEvent) {
    mouseY = e.clientY;
  }
</script>

<div
  role="button"
  tabindex="0"
  onkeypress={() => {}}
  onmousemove={handleMouseMove}
  class="layout-container"
>
  <Nav showNav={showNav}></Nav>

  <main>
   {@render children()}
  </main>
</div>

<style>
  .layout-container {
    position: relative;
    width: 100%;
    height: 100vh;
    overflow: hidden;
    font-family: "Inter";
  }

  main {
    width: 100%;
    height: 100%;
    position: relative;
    overflow: hidden;
  }
</style>
