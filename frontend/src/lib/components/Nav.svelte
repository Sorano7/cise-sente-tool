<script lang="ts">
  let { showNav = true } = $props();
</script>

<nav class:hidden={!showNav}>
  <div class="nav-content">
    <a class="nav-item" href="/">Home</a>
    <a class="nav-item" href="/transit">Transit</a>
    <a class="nav-item" href="/map">Map</a>
  </div>
</nav>

<style>
  nav {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    height: 70px;
    background: rgba(20, 20, 20, 0.9);
    display: flex;
    align-items: center;
    padding: 0 1rem;
    transition: top 0.3s;
    z-index: 1000;
  }

  .hidden {
    top: -60px;
  }

  .nav-content {
    display: flex;
    gap: 1.5rem;
  }

  .nav-item {
    color: white;
    font-weight: 500;
    cursor: pointer;
    transition: color 0.2s;
    text-decoration: none;
  }

  .nav-item:hover {
    color: #ccc;
  }
</style>
