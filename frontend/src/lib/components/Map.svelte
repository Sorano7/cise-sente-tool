<script lang="ts">
  import { onMount, setContext } from "svelte";
  import { loadData, getSystemState } from "$lib/system.svelte";

  const systemState = getSystemState();
  let { fullScreen = false } = $props();

  let canvas: HTMLCanvasElement;
  let ctx: CanvasRenderingContext2D;

  /* -- API Endpoints -- */
  const API_BASE = "http://localhost:8001/api";
  const API_PLANETS = `${API_BASE}`;
  const API_ORBITS = "/orbit_data.json";
  const API_BELTS = "/asteroid_belts.json";
  const API_OBJECTS = `${API_BASE}/objects`;
  const API_PATH_FIND = `${API_BASE}/pathfind`;

  /* -- Map Rendering -- */
  let scale = $state(50);
  let offsetX = $state(0);
  let offsetY = $state(0);
  let startX = $state(0);
  let startY = $state(0);
  const planetRadius = 3;
  const fixedLagrangeSize = 6;

  /* -- Map Controls -- */
  let isPanning = $state(false);
  const minScale = 1;
  const maxScale = 70000;
  let isShiftDown = $state(false);
  let zoomIntensity = $derived.by(() => {
    return isShiftDown ? 0.2 : 0.1;
  });

  /* -- Data points -- */
  let allObjects: string[] = [];
  let orbitalPaths: Record<string, [number, number][]> = {};
  let asteroidBelts: Record<string, [number, number][]> = {};

  /* -- Node selection -- */
  let contextTarget = $derived.by(() => {
    if (!systemState.selectedObject) return null;
    return systemState.selectedObject ? "planet" : "map";
  });
  let contextMenuX = $state(500);
  let contextMenuY = $state(500);
  let selectedObject = "";
  let selectedWaypoint = "";

  let container: HTMLDivElement;

  onMount(() => {
    resizeCanvasToContainer();
    window.addEventListener("resize", resizeCanvasToContainer);
    ctx = canvas.getContext("2d")!;
    if (!ctx) {
      console.error("ctx not found");
    }
    init();

    document.addEventListener("keydown", (e) => {
      if (e.key === "Shift") isShiftDown = true;
    });

    document.addEventListener("keyup", (e) => {
      if (e.key === "Shift") isShiftDown = false;
    });
  });

  /**
   * Resize canvas to match container dimensions
   */
  function resizeCanvasToContainer() {
    if (!canvas) return;
    canvas.width = container.clientWidth;
    canvas.height = container.clientHeight;
    drawAll();
  }

  /**
   * Initialize map.
   * Loads data from API and begin rendering
   */
  async function init() {
    await loadSystemData();
    await systemState.updateObjectPositions();
    fitSystemToCanvas();
    drawAll();
  }

  /**
   * Load map system data from API
   * - `orbitalPaths`
   * - `asteroidBelts`
   * - `allObjects`
   * - `vesselPresets`
   */
  async function loadSystemData() {
    orbitalPaths = await loadData(API_ORBITS);
    asteroidBelts = await loadData(API_BELTS);
    allObjects = await loadData(API_OBJECTS);
  }

  /**
   * Render all objects on canvas
   */
  async function drawAll() {
    if (!ctx) return;

    ctx.clearRect(0, 0, canvas.width, canvas.height);
    ctx.fillStyle = "black";
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    drawAsteroidBelts();
    drawStar();
    drawOrbitalPaths();
    drawPlanets();
    drawScaleBar();
    drawBeltLabels();

    if (systemState.pathResult) {
      await drawPathOnMap();
    }
  }

  // Watch for redraw flag to update map
  $effect(() => {
    if (systemState.needMapRedraw) {
      console.log("[Map] Update detected. Redrawing...");
      systemState.needMapRedraw = false;
      drawAll();
    }
  });

  /**
   * Render orbital paths on canvas
   */
  function drawOrbitalPaths() {
    ctx.strokeStyle = "gray";
    ctx.lineWidth = 0.8;
    ctx.globalAlpha = 0.7;
    for (const orbit of Object.values(orbitalPaths)) {
      ctx.beginPath();
      orbit.forEach(([x, y], i) => {
        const px = canvas.width / 2 + x * scale + offsetX;
        const py = canvas.height / 2 - y * scale + offsetY;
        i === 0 ? ctx.moveTo(px, py) : ctx.lineTo(px, py);
      });
      ctx.stroke();
    }
    ctx.globalAlpha = 1.0;
  }

  /**
   * Render asteroid belts on canvas
   */
  function drawAsteroidBelts() {
    const beltColors: Record<string, string> = {
      inner: "#808080",
      middle: "#707070",
      outer: "#606060",
      scatter: "#707070",
    };

    const beltDistances: Record<string, number> = {
      inner: 4,
      middle: 25,
      outer: 75,
      scatter: 150,
    };

    Object.keys(asteroidBelts).forEach((beltType) => {
      ctx.fillStyle = beltColors[beltType] || "#FFFFFF";

      const beltData = asteroidBelts[beltType];
      const semimajorAxis = beltDistances[beltType] || 5;

      const pointSize = getAsteroidPointSize(scale, semimajorAxis);

      beltData.forEach(([x, y]) => {
        const drawX = canvas.width / 2 + x * scale + offsetX;
        const drawY = canvas.height / 2 - y * scale + offsetY;

        ctx.beginPath();
        ctx.arc(drawX, drawY, pointSize, 0, 2 * Math.PI);
        ctx.fill();
      });
    });
  }

  /**
   * Get the dynamically scaled point size of asteroids
   *
   * @param currentScale current scale of the canvas
   * @param semimajorAxis semimajor axis in AU of the target belt
   */
  function getAsteroidPointSize(
    currentScale: number,
    semimajorAxis: number,
  ): number {
    const baseSize = 1;
    const baseThreshold = 80;

    const dynamicThreshold = baseThreshold * (1 / semimajorAxis);

    if (currentScale < dynamicThreshold) {
      return Math.max(0.3, baseSize * (currentScale / dynamicThreshold));
    } else {
      return baseSize;
    }
  }

  /**
   * Render belt labels
   */
  function drawBeltLabels() {
    const baseThreshold = 80;
    const fadeRange = 20;

    const beltLabels: Record<string, { name: string; distanceAU: number }> = {
      inner: { name: "Tagiyo Raye", distanceAU: 4.0 },
      middle: { name: "Kisekono Raye", distanceAU: 25.0 },
      outer: { name: "Uomo Raye", distanceAU: 75.0 },
    };

    for (const beltType in beltLabels) {
      const { name, distanceAU } = beltLabels[beltType];
      const dynamicThreshold = baseThreshold * (1 / distanceAU);

      let opacity = 0;
      if (scale >= dynamicThreshold) {
        opacity = 1;
      } else if (scale >= dynamicThreshold * 0.5) {
        opacity = (scale - dynamicThreshold * 0.5) / (dynamicThreshold * 0.5);
      }

      if (opacity > 0) {
        const px = canvas.width / 2 + 0 * scale + offsetX;
        const py = canvas.height / 2 + distanceAU * scale + offsetY;

        ctx.globalAlpha = opacity;
        ctx.fillStyle = "#e0e0e0";
        ctx.font = "bold 14px Trebuchet MS";
        ctx.textAlign = "center";
        ctx.fillText(name, px, py);
        ctx.globalAlpha = 1.0;
      }
    }
  }

  /**
   * Render the star
   */
  function drawStar() {
    const au = 0.00434;
    const pxRadius = au * scale;
    const cx = canvas.width / 2 + offsetX;
    const cy = canvas.height / 2 + offsetY;

    ctx.fillStyle = "white";
    ctx.beginPath();
    ctx.arc(cx, cy, pxRadius, 0, 2 * Math.PI);
    ctx.fill();

    ctx.font = "bold 12px Trebuchet MS";
    ctx.fillText("Sente", cx, cy + pxRadius + 12);
  }

  /**
   * Determine if label should be rendered based on scale and semimajor axis
   *
   * @param currentScale current scale
   * @param semimajorAxis semimajor axis in AU
   */
  function shouldShowLabel(
    currentScale: number,
    semimajorAxis: number,
  ): boolean {
    const baseThreshold = 80;
    const dynamicThreshold = semimajorAxis
      ? baseThreshold * (1 / semimajorAxis)
      : baseThreshold;
    return currentScale >= dynamicThreshold;
  }

  /**
   * Determine if planetary systems should be shown as a group based on scale and semimajor axis
   *
   * @param currentScale
   * @param semimajorAxis
   */
  function showAsGroup(currentScale: number, semimajorAxis: number): boolean {
    const baseThreshold = 500;
    const dynamicThreshold = semimajorAxis
      ? baseThreshold * (1 / semimajorAxis)
      : baseThreshold;
    return currentScale < dynamicThreshold;
  }

  /**
   * Draw objects on map
   */
  function drawPlanets() {
    const planetGroups: Record<
      string,
      {
        members: string[];
        center: { x: number; y: number };
        semimajor: number;
      }
    > = {};

    for (const [name, obj] of Object.entries(systemState.allObjects)) {
      if (obj.type === "planet") {
        planetGroups[name] = {
          members: [],
          center: { x: obj.x, y: obj.y },
          semimajor: obj.a,
        };
      }
    }

    for (const [name, obj] of Object.entries(systemState.allObjects)) {
      const { type } = obj;

      if (type.startsWith("orbital_") || type.startsWith("lagrange_orbital_")) {
        const parts = type.split("_");
        const primaryName = parts[parts.length - 1];

        if (planetGroups[primaryName]) {
          planetGroups[primaryName].members.push(name);
        }
      }
    }

    for (const planetName in planetGroups) {
      planetGroups[planetName].members.push(planetName);
    }

    for (const [name, { x, y, type, a }] of Object.entries(systemState.allObjects)) {
      const isOrigin = name === systemState.path.origin;
      const isDestination = name === systemState.path.destination;
      const waypointIndex = systemState.path.waypoints.indexOf(name);
      const isWaypoint = waypointIndex !== -1;
      let highlightColor = null;
      let labelPrefix = "";

      if (isOrigin || isDestination) {
        highlightColor = isOrigin ? "green" : "red";
      }
      if (isOrigin) {
        highlightColor = "green";
        labelPrefix = "0: ";
      } else if (isDestination) {
        highlightColor = "red";
        labelPrefix = `${systemState.path.waypoints.length + 1}: `;
      } else if (isWaypoint) {
        highlightColor = "blue";
        labelPrefix = `${waypointIndex + 1}: `;
      }

      const isLagrange = type.startsWith("lagrange");
      const isMoon = type.startsWith("orbital");
      const isDwarf = type === "dwarf";

      const groupKey = Object.entries(planetGroups).find(([_, g]) =>
        g.members.includes(name),
      )?.[0];

      let new_a = a || 0;

      if (groupKey && isMoon) {
        new_a = planetGroups[groupKey].semimajor;
      }

      if (groupKey && showAsGroup(scale, new_a)) {
        if (name !== groupKey) {
          continue;
        }

        const group = planetGroups[groupKey];
        const px = canvas.width / 2 + group.center.x * scale + offsetX;
        const py = canvas.height / 2 - group.center.y * scale + offsetY;

        ctx.fillStyle = highlightColor || "white";
        ctx.beginPath();
        ctx.arc(px, py, planetRadius + 1, 0, 2 * Math.PI);
        ctx.fill();

        if (shouldShowLabel(scale, new_a)) {
          ctx.fillStyle = highlightColor || "white";
          ctx.font = "12px Trebuchet MS";
          ctx.fillText(`${labelPrefix}${groupKey}`, px + 8, py - 8);
        }
      } else {
        // Draw normally
        const px = canvas.width / 2 + x * scale + offsetX;
        const py = canvas.height / 2 - y * scale + offsetY;

        if (highlightColor) {
          ctx.fillStyle = highlightColor;
        } else if (isLagrange) {
          ctx.fillStyle = "#b3b3b3";
        } else if (isMoon) {
          ctx.fillStyle = "#d3d3d3";
        } else if (isDwarf) {
          ctx.fillStyle = "#d3d3d3";
        } else {
          ctx.fillStyle = "white";
        }

        if (isLagrange) {
          ctx.beginPath();
          ctx.moveTo(px, py - fixedLagrangeSize / 2);
          ctx.lineTo(px + fixedLagrangeSize / 2, py);
          ctx.lineTo(px, py + fixedLagrangeSize / 2);
          ctx.lineTo(px - fixedLagrangeSize / 2, py);
          ctx.closePath();
          ctx.fill();
        } else if (isMoon) {
          ctx.beginPath();
          ctx.arc(px, py, planetRadius * 0.75, 0, 2 * Math.PI);
          ctx.fill();
        } else {
          ctx.beginPath();
          ctx.arc(px, py, planetRadius, 0, 2 * Math.PI);
          ctx.fill();
        }

        if (shouldShowLabel(scale, new_a)) {
          ctx.fillStyle = highlightColor || "white";
          ctx.font = isMoon ? "11px Trebuchet MS" : "12px Trebuchet MS";
          ctx.fillText(`${labelPrefix}${name}`, px + 8, py - 8);
        }
      }
    }
  }

  /**
   * Render scale bar on the map
   */
  function drawScaleBar() {
    const barLength = 100;
    const au = barLength / scale;
    const km = au * 1.496e8;
    const startX = 20;
    const endX = startX + barLength;
    const y = canvas.height - 30;

    ctx.strokeStyle = "white";
    ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.moveTo(startX, y);
    ctx.lineTo(endX, y);
    ctx.stroke();

    ctx.fillStyle = "white";
    ctx.font = "12px Trebuchet MS";
    ctx.textAlign = "center";
    let scaleText =
      au.toFixed(2) === "0.01" ? `${km.toFixed(0)} km` : `${au.toFixed(2)} AU`;

    ctx.fillText(scaleText, (startX + endX) / 2, y - 8);

    ctx.textAlign = "start";
  }

  /**
   * Render the current `pathResult` on map
   * - Draw each node at the arrival time and a cyan line connecting each
   */
  async function drawPathOnMap() {
    if (!systemState.hasValidPath()) return;

    let currentTimeUnix = Math.round(systemState.path.launchTimeUnix);
    const points: { x: number; y: number; name: string }[] = [];

    const originName = systemState.pathResult!.origin;
    const originPosition = await systemState.getArrivalPosition(originName, currentTimeUnix);
    if (originPosition) points.push({ ...originPosition, name: originName });

    for (const leg of systemState.pathResult!.legs) {
      const destinationName = leg.destination;
      const travelSeconds = leg.total_time || 0;
      currentTimeUnix += travelSeconds;

      const destPos = await systemState.getArrivalPosition(destinationName, currentTimeUnix);
      if (!destPos) continue;

      points.push({ ...destPos, name: destinationName });
    }

    if (points.length < 2) {
      console.warn("[drawPathOnMap] Not enough points to draw a line");
      return;
    }

    // Draw path
    ctx.strokeStyle = "cyan";
    ctx.lineWidth = 2;
    ctx.beginPath();

    points.forEach((pos, index) => {
      const px = canvas.width / 2 + pos.x * scale + offsetX;
      const py = canvas.height / 2 - pos.y * scale + offsetY;

      if (index === 0) {
        ctx.moveTo(px, py);
      } else {
        ctx.lineTo(px, py);
      }
    });

    ctx.stroke();

    // Draw markers and labels
    for (let i = 0; i < points.length; i++) {
      const isOrigin = i === 0;
      const color = isOrigin ? "green" : "red";
      const pos = points[i];
      const px = canvas.width / 2 + pos.x * scale + offsetX;
      const py = canvas.height / 2 - pos.y * scale + offsetY;

      ctx.fillStyle = color;
      ctx.beginPath();
      ctx.arc(px, py, 4, 0, 2 * Math.PI);
      ctx.fill();

      if (!isOrigin) {
        ctx.fillStyle = color;
        ctx.font = "bold 12px Trebuchet MS";
        ctx.fillText(`${i}: ${pos.name}`, px + 6, py - 6);
      }
    }
  }

  /**
   * Fit path to view
   */
  async function fitPathToView() {
    if (!systemState.hasValidPath()) return;

    let currentTimeUnix = Math.round(systemState.getUnixTimestamp());
    const points: { x: number; y: number }[] = [];

    const originName = systemState.pathResult!.origin;
    const originPos = await systemState.getArrivalPosition(originName, currentTimeUnix);
    if (originPos) points.push(originPos);

    for (const leg of systemState.pathResult!.legs) {
      const destinationName = leg.destination;
      const travelSeconds = (leg.total_time_days || 0) * 86400;
      currentTimeUnix += travelSeconds;
      const destKey = `${destinationName}_${currentTimeUnix}`;
      const destPos = await systemState.getArrivalPosition(destinationName, currentTimeUnix);
      if (destPos) points.push(destPos);
    }

    if (
      points.length === 0 ||
      points.some((p) => p == null || !isFinite(p.x) || !isFinite(p.y))
    ) {
      console.warn("[fitPathToView] Invalid or missing point data:", points);
      return;
    }

    // Calculate bounding box
    const xs = points.map((p) => p.x);
    const ys = points.map((p) => p.y);

    const minX = Math.min(...xs);
    const maxX = Math.max(...xs);
    const minY = Math.min(...ys);
    const maxY = Math.max(...ys);

    // Center point
    const centerX = (minX + maxX) / 2;
    const centerY = (minY + maxY) / 2;

    // Compute required scale
    const margin = 1.2;
    const rangeX = (maxX - minX) * margin;
    const rangeY = (maxY - minY) * margin;

    if (!isFinite(rangeX) || !isFinite(rangeY) || rangeX <= 0 || rangeY <= 0) {
      console.warn("[fitPathToView] Invalid bounding range:", rangeX, rangeY);
      return;
    }

    const canvasWidthInAU = canvas.width / scale;
    const canvasHeightInAU = canvas.height / scale;

    // New scale to fit width or height
    const scaleX = canvas.width / rangeX;
    const scaleY = canvas.height / rangeY;
    const newScale = Math.min(scaleX, scaleY);

    scale = Math.max(5, Math.min(newScale, maxScale));

    // Center offsets
    offsetX = -(centerX * scale);
    offsetY = centerY * scale;

    drawAll();
  }

  function handleMouseDown(e: MouseEvent) {
    switch (e.button) {
      case 0:
        isPanning = true;
        systemState.showContextMenu = false;
        startX = e.clientX - offsetX;
        startY = e.clientY - offsetY;
        break;

      case 2:
        const rect = canvas.getBoundingClientRect();
        const mouseX = e.clientX - rect.left;
        const mouseY = e.clientY - rect.top;

        for (const [name, { x, y }] of Object.entries(systemState.allObjects)) {
          const px = canvas.width / 2 + x * scale + offsetX;
          const py = canvas.height / 2 - y * scale + offsetY;

          const distance = Math.hypot(mouseX - px, mouseY - py);

          if (distance < 8) {
            systemState.selectedObject = name;
            contextMenuX = e.clientX;
            contextMenuY = e.clientY;
            systemState.showContextMenu = true;
            contextTarget = "planet";
            break;
          }
        }
        if (!systemState.selectedObject) {
          contextTarget = "map";
          contextMenuX = e.clientX;
          contextMenuY = e.clientY;
          systemState.showContextMenu = true;
        }
        break;
    }
  }

  $effect(() => {
    if (!systemState.showContextMenu) {
      contextMenuX = canvas.width / 2;
      contextMenuY = canvas.height / 2;
    }
  })

  function handleMouseMove(e: MouseEvent) {
    if (!isPanning) return;
    offsetX = e.clientX - startX;
    offsetY = e.clientY - startY;
    drawAll();
  }

  function handleMouseUp() {
    isPanning = false;
  }

  function handleWheel(e: WheelEvent) {
    systemState.showContextMenu = false;
    e.preventDefault();
    const rect = canvas.getBoundingClientRect();
    const mx = e.clientX - rect.left;
    const my = e.clientY - rect.top;

    const worldX = (mx - canvas.width / 2 - offsetX) / scale;
    const worldY = (my - canvas.height / 2 - offsetY) / scale;

    let intensity = isShiftDown ? zoomIntensity * 3 : zoomIntensity;
    const zoom = e.deltaY < 0 ? 1 + intensity : 1 - intensity;
    const newScale = Math.min(maxScale, Math.max(minScale, scale * zoom));

    const worldXNew = worldX * newScale;
    const worldYNew = worldY * newScale;

    offsetX -= worldXNew - worldX * scale;
    offsetY -= worldYNew - worldY * scale;

    scale = newScale;
    drawAll();
  }

  function fitSystemToCanvas() {
    scale = minScale;
    offsetX = 0;
    offsetY = 0;

    drawAll();
  }

  function selectPlanet(type: "origin" | "destination" | "waypoint") {
    if (!systemState.selectedObject) return;
    systemState.AddObjectToPath(systemState.selectedObject, type);
    systemState.selectedObject = null;
    systemState.showContextMenu = false;
    drawAll();
  }

  // TODO: test
  let updateWaypoint = $derived.by(() => {
    selectedWaypoint;
    addWaypoint();
  });

  function addWaypoint() {
    systemState.AddWaypoint(selectedWaypoint);
    selectedWaypoint = "";
    drawAll();
  }

  function removeWaypoint(index: number) {
    systemState.RemoveWaypointByIndex(index);
    drawAll();
  }

  function removeFromRoute(name: string | null) {
    if (!name) return;

    systemState.RemoveObjectFromPath(name);
    drawAll();
  }

  function focusOnPlanet() {
    if (!systemState.selectedObject || !systemState.isValidObject(systemState.selectedObject)) return;

    const obj = systemState.getObjectByName(systemState.selectedObject);

    const targetZoom = 3000;

    offsetX = -(obj.x * targetZoom);
    offsetY = obj.y * targetZoom;

    const startScale = scale;
    const endScale = Math.min(targetZoom, maxScale);
    const steps = 20;

    let step = 0;
    const zoomInterval = setInterval(() => {
      step++;
      scale = startScale + (endScale - startScale) * (step / steps);

      drawAll();

      if (step >= steps) {
        clearInterval(zoomInterval);
      }
    }, 16);
  }

  $effect(() => {
    if (systemState.focusOnObject) {
      focusOnPlanet();
      systemState.focusOnObject = false;
    }
  })

  function saveMap() {
    const link = document.createElement("a");
    const time = systemState.timestamp.toFixed(0)
    link.download = `cise-sente_${time}.png`;
    link.href = canvas.toDataURL("image/png");
    link.click();
  }
</script>

<div class={fullScreen ? "canvas-container-full" : "canvas-container"} bind:this={container}>
  <canvas
    bind:this={canvas}
    onmousedown={handleMouseDown}
    oncontextmenu={(e) => e.preventDefault()}
    onmousemove={handleMouseMove}
    onmouseup={handleMouseUp}
    onmouseleave={handleMouseUp}
    onwheel={handleWheel}
    style="background-color: black; width: 100%; height: 100%"
  ></canvas>
  <div class="map-controls">
    <button onclick={fitSystemToCanvas}>System View</button>
    {#if !fullScreen}
      <button onclick={fitPathToView}>Focus Path</button>
    {/if}
    <button onclick={saveMap}>Save Map</button>
  </div>
  {#if systemState.showContextMenu}
    <div
      class="context-menu"
      style="top: {contextMenuY}px; left: {contextMenuX}px;"
    >
      {#if contextTarget === "planet" && systemState.selectedObject}
        <div
          role="button"
          tabindex="0"
          onkeypress={() => {}}
          class="context-option"
          onclick={() => {;
            focusOnPlanet();
            systemState.showContextMenu = false;
          }}
        >
          Focus
        </div>
        {#if !fullScreen}
        <div
          role="button"
          tabindex="0"
          onkeypress={() => {}}
          class="context-option"
          onclick={() => selectPlanet("origin")}
        >
          Set as Origin
        </div>
        <div
          role="button"
          tabindex="0"
          onkeypress={() => {}}
          class="context-option"
          onclick={() => selectPlanet("destination")}
        >
          Set as Destination
        </div>
        <div
          role="button"
          tabindex="0"
          onkeypress={() => {}}
          class="context-option"
          onclick={() => selectPlanet("waypoint")}
        >
          Add as Waypoint
        </div>
        <div
          role="button"
          tabindex="0"
          onkeypress={() => {}}
          class="context-option"
          onclick={() => {
            removeFromRoute(systemState.selectedObject);
            systemState.showContextMenu = false;
          }}
        >
          Remove from Route
        </div>
        {/if}
      {:else if contextTarget === "map"}
        <div
          role="button"
          tabindex="0"
          onkeypress={() => {}}
          class="context-option"
          onclick={() => {
            systemState.clearPath();
            systemState.showContextMenu = false;
            drawAll();
          }}
        >
          Clear Selection
        </div>
      {/if}
    </div>
  {/if}
</div>

<style>
  .canvas-container {
    flex: 1 1 auto;
    overflow: hidden;
    position: relative;
  }

  .canvas-container-full {
    min-height: 100vh;
    min-width: 100vw;
    flex: 1 1 auto;
  }

  /* Narrow Mode */
  @media (max-width: 1499px) {
    .canvas-container {
      flex: 0 0 auto;
      max-height: 55vh;
    }
  }

  /* Wide Layout */
  @media (min-width: 1500px) {
    .canvas-container {
      flex: 1 1 auto;
      overflow: hidden;
      display: flex;
      align-items: center;
    }
  }

  .map-controls {
    position: absolute;
    bottom: 1rem;
    right: 1rem;
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
    z-index: 10;
  }

  .map-controls button {
    background: #222;
    color: white;
    border: 1px solid #444;
    padding: 0.4rem 0.8rem;
    font-size: 0.85rem;
    border-radius: 4px;
    cursor: pointer;
    transition: background 0.2s;
  }

  .map-controls button:hover {
    background: #333;
  }

  .context-menu {
    position: fixed;
    background: #333;
    border: 1px solid #555;
    padding: 4px;
    border-radius: 6px;
    z-index: 1000;
  }

  .context-option {
    padding: 6px 12px;
    color: white;
    cursor: pointer;
  }

  .context-option:hover {
    background-color: #555;
  }
</style>
