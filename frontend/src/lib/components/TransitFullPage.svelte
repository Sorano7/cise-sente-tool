<script lang="ts">
    import { onMount } from "svelte";

    let canvas: HTMLCanvasElement;
    let ctx: CanvasRenderingContext2D;

    const TIMESTAMP_OFFSET = 23164249536;

    /* -- API URLs -- */
    const API_BASE = "http://localhost:8001/api";
    const API_PLANETS = `${API_BASE}`;
    const API_ORBITS = "/orbit_data.json";
    const API_BELTS = "/asteroid_belts.json";
    const API_OBJECTS = `${API_BASE}/objects`;
    const API_PATH_FIND = `${API_BASE}/pathfind`;
    const API_VESSELS = `${API_BASE}/vessels`;
    const API_CLOCK = `${API_BASE}/datetime`;

    /* -- Canvas -- */
    let scale = 50;
    let offsetX = 0;
    let offsetY = 0;
    let isPanning = false;
    let startX = 0;
    let startY = 0;

    const planetRadius = 3;
    const fixedLagrangeSize = 6;
    const minScale = 1;
    const maxScale = 70000;
    let isShiftDown = false;
    let zoomIntensity = 0.1;

    /* -- Data points -- */
    let allObjects: string[] = [];

    let orbitalPaths: Record<string, [number, number][]> = {};

    let asteroidBelts: Record<string, [number, number][]> = {};

    let lastPlanetData: Record<
        string,
        { x: number; y: number; z?: number; type: string; a: number }
    > = {};

    const arrivalPositions: Map<string, { x: number; y: number }> = new Map();

    /* -- Vessel specs -- */
    let selectedPreset = "";
    let deltaV = 3300000;
    let massT = 250;
    let thrustN = 1780000;
    let vesselPresets: Record<
        string,
        { delta_v: number; mass_t: number; thrust_n: number }
    > = {};

    /* -- Search policy -- */
    let timeWeight = 1;
    let costWeight = 1;
    let comfortWeight = 1;
    let disableCoast = false;

    /* -- Transit settings -- */
    let origin = "";
    let destination = "";
    let waypoints: string[] = [];
    let selectedWaypoint = "";

    /* -- Time controls -- */
    let currentTimestamp = Math.floor(Date.now() / 1000);
    let launcTimeDisplay = "";
    let launchTimeInput = (currentTimestamp + TIMESTAMP_OFFSET).toString();

    /* -- Pathfinding -- */
    let pathResult: any = null;

    /* -- Node selection -- */
    let clickedPlanet: string | null = null;
    let contextTarget: "planet" | "map" | null = null;
    let showContextMenu = false;
    let contextMenuX = 0;
    let contextMenuY = 0;

    /* -- Object tools -- */
    let selectedObject = "";

    /* -- Clock -- */
    interface CalendarDisplay {
        segments: number[];
        separators: string[];
        rules: (number | null)[];
        digits: number[];
    }

    interface WorldClockResponse {
        timestamp: number;
        meaji: CalendarDisplay;
        imor: CalendarDisplay;
        junesgi: CalendarDisplay;
        earth: string;
    }

    let timestamp = 0;
    let earthTime = "";
    let meaji: CalendarDisplay;
    let imor: CalendarDisplay;
    let junesgi: CalendarDisplay;

    let lastSync = 0;

    onMount(async () => {
        resizeCanvasToContainer();
        window.addEventListener("resize", resizeCanvasToContainer);
        ctx = canvas.getContext("2d")!;
        if (!ctx) {
            console.error("ctx not found");
        }
        init();

        await syncClock();
        setInterval(tickClock, 1000);
        setInterval(() => syncClock(), 300000);

        document.addEventListener("keydown", (e) => {
            if (e.key === "Shift") isShiftDown = true;
        });

        document.addEventListener("keyup", (e) => {
            if (e.key === "Shift") isShiftDown = false;
        });
    });

    /**
     * Sync clock with API
     */
    async function syncClock() {
        const data: WorldClockResponse = await loadData(`${API_CLOCK}/init`);

        timestamp = Math.round(data.timestamp);
        earthTime = data.earth;
        meaji = data.meaji;
        imor = data.imor;
        junesgi = data.junesgi;

        lastSync = Date.now();
    }

    /**
     * Increment current time by 1. Request sync if unable to increment.
     */
    function tickClock() {
        if (!meaji || !imor || !junesgi) return;

        timestamp += 1;
        const earthDate = new Date((timestamp - TIMESTAMP_OFFSET) * 1000);
        earthTime = formatEarthDate(earthDate);

        if (!incrementCalendar(meaji)) syncClock();
        if (!incrementCalendar(imor)) syncClock();
        if (!incrementCalendar(junesgi)) syncClock();
    }

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
        meaji = { ...meaji };
        imor = { ...imor };
        junesgi = { ...junesgi };
        return true;
    }

    /**
     * Pad the start of a number with 0 based on target length
     *
     * @param num Number to process
     * @param length Target length
     */
    function pad(num: number, length: number) {
        return length > 0
            ? num.toString().padStart(length, "0")
            : num.toString();
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

    /**
     * Restore saved state
     */
    async function restoreState() {
        const savedOptions = localStorage.getItem("savedTripOptions");
        const savedPath = localStorage.getItem("savedPathResult");

        if (savedOptions) {
            const options = JSON.parse(savedOptions);
            origin = options.origin;
            destination = options.destination;
            currentTimestamp = options.currentTimestamp;
            deltaV = options.deltaV;
            massT = options.massT;
            thrustN = options.thrustN;
            timeWeight = options.timeWeight;
            costWeight = options.costWeight;
            comfortWeight = options.comfortWeight;
            disableCoast = options.disableCoast;
            selectedPreset = options.selectedPreset;
            launchTimeInput = options.launchTimeInput;
            waypoints = options.waypoints || [];
        }

        if (savedPath) {
            pathResult = JSON.parse(savedPath);
            await fitPathToView;
            await convertTime(currentTimestamp);
        }
    }

    /**
     * Initialize map.
     * Loads data from API and begin rendering
     */
    async function init() {
        await loadSystemData();
        await fetchPlanetPositions();
        fitSystemToCanvas();
        drawAll();
        await restoreState();
    }

    /**
     * Resize canvas to match container dimensions
     */
    function resizeCanvasToContainer() {
        if (!canvas) return;
        canvas.width = canvas.clientWidth;
        canvas.height = canvas.clientHeight;
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
        vesselPresets = await loadData(`${API_VESSELS}/presets`);
    }

    /**
     * Load data from API
     *
     * @param url API endpoint
     * @returns json data
     */
    async function loadData(url: string) {
        try {
            const res = await fetch(url);
            if (!res.ok) throw new Error("Fetch failed");
            return await res.json();
        } catch (error) {
            console.error(`Failed to fetch ${url}: ${error}`);
        }
    }

    /**
     * Load planet positions from API using `currentTimestamp`
     * @modifies `lastPlanetData`
     */
    async function fetchPlanetPositions() {
        const res = await fetch(
            `${API_PLANETS}/positions?timestamp=${currentTimestamp}`,
        );
        lastPlanetData = await res.json();
    }

    /**
     * Post a path calculation request to API
     * @modifies `pathResult`
     */
    async function calculatePath() {
        if (!origin || !destination) {
            alert("Please select both origin and destination.");
            return;
        }

        arrivalPositions.clear();

        await convertTime(currentTimestamp);

        const requestData = {
            vessel: {
                delta_v: deltaV,
                mass_t: massT,
                thrust_n: thrustN,
            },
            policy: {
                time_weight: timeWeight,
                cost_weight: costWeight,
                comfort_weight: comfortWeight,
                disable_coast: disableCoast,
            },
            origin,
            destination,
            mandatory_stops: waypoints,
            launch_time: currentTimestamp,
        };

        console.log(requestData);

        try {
            const response = await fetch(API_PATH_FIND, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify(requestData),
            });

            if (!response.ok) {
                throw new Error("Pathfinding request failed.");
            }

            pathResult = await response.json();
            saveState();
        } catch (error) {
            console.error("Pathfinding error:", error);
            alert("Failed to calculate path.");
        }

        await applyLaunchTime();
        await fitPathToView();
        await drawAll();
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

        if (pathResult) {
            await drawPathOnMap();
        }
    }

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
     * Render belt labels
     */
    function drawBeltLabels() {
        const baseThreshold = 80;
        const fadeRange = 20;

        const beltLabels: Record<string, { name: string; distanceAU: number }> =
            {
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
                opacity =
                    (scale - dynamicThreshold * 0.5) / (dynamicThreshold * 0.5);
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

        for (const [name, obj] of Object.entries(lastPlanetData)) {
            if (obj.type === "planet") {
                planetGroups[name] = {
                    members: [],
                    center: { x: obj.x, y: obj.y },
                    semimajor: obj.a,
                };
            }
        }

        for (const [name, obj] of Object.entries(lastPlanetData)) {
            const { type } = obj;

            if (
                type.startsWith("orbital_") ||
                type.startsWith("lagrange_orbital_")
            ) {
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

        for (const [name, { x, y, type, a }] of Object.entries(
            lastPlanetData,
        )) {
            const isOrigin = name === origin;
            const isDestination = name === destination;
            const waypointIndex = waypoints.indexOf(name);
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
                labelPrefix = `${waypoints.length + 1}: `;
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
                    ctx.font = isMoon
                        ? "11px Trebuchet MS"
                        : "12px Trebuchet MS";
                    ctx.fillText(`${labelPrefix}${name}`, px + 8, py - 8);
                }
            }
        }
    }

    function getMoonPrimary(moon: string) {
        const moonObj = lastPlanetData[moon];
        if (!moonObj.type.startsWith("orbital")) return null;

        const primaryName = moonObj.type.split("-")[1];
        const primaryObj = lastPlanetData[primaryName];

        return primaryObj;
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
            au.toFixed(2) === "0.01"
                ? `${km.toFixed(0)} km`
                : `${au.toFixed(2)} AU`;

        ctx.fillText(scaleText, (startX + endX) / 2, y - 8);

        ctx.textAlign = "start";
    }

    /**
     * Render the current `pathResult` on map
     * - Draw each node at the arrival time and a cyan line connecting each
     */
    async function drawPathOnMap() {
        if (!pathResult || !pathResult.legs || pathResult.legs.length === 0) {
            return;
        }

        let currentTime = Math.round(currentTimestamp);
        const points: { x: number; y: number; name: string }[] = [];

        const originName = pathResult.origin;
        const originKey = `${originName}_${currentTime}`;

        if (!arrivalPositions.has(originKey)) {
            const pos = await fetchPositionAtTime(originName, currentTime);
            if (pos) arrivalPositions.set(originKey, { x: pos.x, y: pos.y });
        }

        const originPosition = arrivalPositions.get(originKey);
        if (!originPosition) {
            return;
        }
        points.push({ ...originPosition, name: originName });

        for (const leg of pathResult.legs) {
            const destinationName = leg.destination;
            const travelSeconds = leg.total_time || 0;
            currentTime += travelSeconds;
            const destKey = `${destinationName}_${currentTime}`;

            if (!arrivalPositions.has(destKey)) {
                const pos = await fetchPositionAtTime(
                    destinationName,
                    currentTime,
                );
                if (pos) arrivalPositions.set(destKey, { x: pos.x, y: pos.y });
            }

            const destPos = arrivalPositions.get(destKey);
            if (!destPos) {
                continue;
            }

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
        if (!pathResult || !pathResult.legs || pathResult.legs.length === 0)
            return;

        let currentTime = Math.round(currentTimestamp);
        const points: { x: number; y: number }[] = [];

        const originName = pathResult.origin;
        const originKey = `${originName}_${currentTime}`;

        if (!arrivalPositions.has(originKey)) {
            const pos = await fetchPositionAtTime(originName, currentTime);
            if (pos) arrivalPositions.set(originKey, { x: pos.x, y: pos.y });
        }

        const originPos = arrivalPositions.get(originKey);
        if (!originPos) return;
        points.push(originPos);

        for (const leg of pathResult.legs) {
            const destinationName = leg.destination;
            const travelSeconds = (leg.total_time_days || 0) * 86400;
            currentTime += travelSeconds;
            const destKey = `${destinationName}_${currentTime}`;

            if (!arrivalPositions.has(destKey)) {
                const pos = await fetchPositionAtTime(
                    destinationName,
                    currentTime,
                );
                if (pos) arrivalPositions.set(destKey, { x: pos.x, y: pos.y });
            }

            const destPos = arrivalPositions.get(destKey);
            if (destPos) points.push(destPos);
        }

        if (
            points.length === 0 ||
            points.some((p) => p == null || !isFinite(p.x) || !isFinite(p.y))
        ) {
            console.warn(
                "[fitPathToView] Invalid or missing point data:",
                points,
            );
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

        if (
            !isFinite(rangeX) ||
            !isFinite(rangeY) ||
            rangeX <= 0 ||
            rangeY <= 0
        ) {
            console.warn(
                "[fitPathToView] Invalid bounding range:",
                rangeX,
                rangeY,
            );
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

    /**
     * Fetch position of an object at the given time
     *
     * @param name
     * @param timestamp
     */
    async function fetchPositionAtTime(name: string, timestamp: number) {
        try {
            const res = await fetch(
                `${API_PLANETS}/position?name=${encodeURIComponent(name)}&timestamp=${timestamp}`,
            );
            if (!res.ok) {
                console.error(
                    `[fetchPositionAtTime] Fetch failed for ${name} at ${timestamp}:`,
                    res.statusText,
                );
                return null;
            }

            const data = await res.json();
            console.log(`[fetchPositionAtTime] Success:`, data);
            return data;
        } catch (err) {
            console.error(
                `[fetchPositionAtTime] Error for ${name} at ${timestamp}:`,
                err,
            );
            return null;
        }
    }

    function handleMouseDown(e: MouseEvent) {
        switch (e.button) {
            case 0:
                isPanning = true;
                showContextMenu = false;
                startX = e.clientX - offsetX;
                startY = e.clientY - offsetY;
                break;

            case 2:
                const rect = canvas.getBoundingClientRect();
                const mouseX = e.clientX - rect.left;
                const mouseY = e.clientY - rect.top;

                for (const [name, { x, y }] of Object.entries(lastPlanetData)) {
                    const px = canvas.width / 2 + x * scale + offsetX;
                    const py = canvas.height / 2 - y * scale + offsetY;

                    const distance = Math.hypot(mouseX - px, mouseY - py);

                    if (distance < 8) {
                        clickedPlanet = name;
                        contextMenuX = e.clientX;
                        contextMenuY = e.clientY;
                        showContextMenu = true;
                        contextTarget = "planet";
                        break;
                    }
                }
                if (!clickedPlanet) {
                    contextTarget = "map";
                    contextMenuX = e.clientX;
                    contextMenuY = e.clientY;
                    showContextMenu = true;
                }
                break;
        }
    }

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
        showContextMenu = false;
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

    function handleKey(e: KeyboardEvent) {
        if (e.repeat) return;
        if (e.key === "Shift") {
            isShiftDown = true;
            zoomIntensity = 1.0;
        }
    }

    function handleKeyUp(e: KeyboardEvent) {
        if (e.key === "Shift") {
            isShiftDown = false;
            zoomIntensity = 0.1;
        }
    }

    function clearPath() {
        origin = "";
        destination = "";
        waypoints = [];
        pathResult = null;
        arrivalPositions.clear();
        localStorage.removeItem("savedPathResult");
        saveState();
        drawAll();
    }

    function selectPlanet(type: "origin" | "destination" | "waypoint") {
        if (!clickedPlanet) return;

        if (type === "origin") {
            if (clickedPlanet === destination) destination = "";
            waypoints = waypoints.filter((wp) => wp !== clickedPlanet);
            origin = clickedPlanet;
        } else if (type === "destination") {
            if (clickedPlanet === origin) origin = "";
            waypoints = waypoints.filter((wp) => wp !== clickedPlanet);
            destination = clickedPlanet;
        } else if (type === "waypoint") {
            if (clickedPlanet === origin) origin = "";
            if (clickedPlanet === destination) destination = "";
            if (!waypoints.includes(clickedPlanet)) {
                waypoints = [...waypoints, clickedPlanet];
            }
        }

        saveState();
        clickedPlanet = null;
        showContextMenu = false;
        drawAll();
    }

    function applyVesselPreset() {
        if (selectedPreset && vesselPresets[selectedPreset]) {
            const preset = vesselPresets[selectedPreset];
            deltaV = preset.delta_v;
            massT = preset.mass_t;
            thrustN = preset.thrust_n;
        }
    }

    function saveState() {
        localStorage.setItem(
            "savedTripOptions",
            JSON.stringify({
                origin,
                destination,
                currentTimestamp,
                deltaV,
                massT,
                thrustN,
                timeWeight,
                costWeight,
                comfortWeight,
                disableCoast,
                selectedPreset,
                launchTimeInput,
                waypoints,
            }),
        );

        if (pathResult) {
            localStorage.setItem("savedPathResult", JSON.stringify(pathResult));
        }
    }

    async function convertTime(timestamp: number) {
        const data = await loadData(
            `${API_CLOCK}/convert?timestamp=${timestamp}`,
        );
        launcTimeDisplay = `${data.timestamp} (${data.meaji})`;
    }

    async function applyLaunchTime() {
        try {
            const res = await fetch(
                `${API_CLOCK}/parse?input=${encodeURIComponent(launchTimeInput)}`,
            );
            const data = await res.json();

            if (data.timestamp) {
                currentTimestamp = parseFloat(data.timestamp);
                if (launchTimeInput === "") {
                    launchTimeInput = Math.round(
                        currentTimestamp + TIMESTAMP_OFFSET,
                    ).toString();
                }

                await fetchPlanetPositions();
                await drawAll();
                convertTime(currentTimestamp);
            } else {
                console.error("Invalid timestamp response:", data);
            }
        } catch (err) {
            console.error("Error parsing launch time:", err);
        }
    }

    function addWaypoint() {
        if (
            selectedWaypoint &&
            !waypoints.includes(selectedWaypoint) &&
            selectedWaypoint !== origin &&
            selectedWaypoint !== destination
        ) {
            waypoints = [...waypoints, selectedWaypoint];
            selectedWaypoint = "";
            saveState();
            drawAll();
        }
    }

    function removeWaypoint(index: number) {
        waypoints = waypoints.filter((_, i) => i !== index);
        saveState();
        drawAll();
    }

    function removeFromRoute(name: string | null) {
        if (!name) return;

        if (name === origin) {
            origin = "";
        } else if (name === destination) {
            destination = "";
        } else {
            const index = waypoints.indexOf(name);
            if (index !== -1) {
                removeWaypoint(index);
            }
        }
        saveState();
        drawAll();
    }

    $: if (selectedWaypoint) {
        addWaypoint();
    }

    function showTransitMenu() {
        if (!selectedObject || !lastPlanetData[selectedObject]) return;

        const centerX = canvas.width / 2 + offsetX;
        const centerY = canvas.height / 2 + offsetY;

        clickedPlanet = selectedObject;
        contextMenuX = centerX;
        contextMenuY = centerY;
        showContextMenu = true;
        contextTarget = "planet";
    }

    function focusOnPlanet() {
        if (!selectedObject || !lastPlanetData[selectedObject]) return;

        const obj = lastPlanetData[selectedObject];

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

    function getRandomObject() {
        if (!lastPlanetData) return;

        const objs = Object.keys(lastPlanetData);
        const randomObj = objs[Math.floor(Math.random() * objs.length)];
        return randomObj;
    }

    function saveMap() {
        const link = document.createElement("a");
        link.download = `cise-sente_${(currentTimestamp + TIMESTAMP_OFFSET).toFixed(0)}.png`;
        link.href = canvas.toDataURL("image/png");
        link.click();
    }
</script>

<div class="page-layout">
    <div class="clock-panel">
        <h4>System Clock</h4>
        <div class="clock-container">
            {#if meaji && imor && junesgi}
                <div class="clock-group">
                    <div class="clock-label">Timestamp</div>
                    <div class="clock-value">{timestamp}</div>
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
    </div>

    <div class="main-container">
        <div class="left-panel">
            <div class="canvas-container">
                <canvas
                    bind:this={canvas}
                    on:mousedown|preventDefault={handleMouseDown}
                    on:contextmenu|preventDefault
                    on:mousemove={handleMouseMove}
                    on:mouseup={handleMouseUp}
                    on:mouseleave={handleMouseUp}
                    on:wheel={handleWheel}
                    on:keydown={handleKey}
                    on:keyup={handleKeyUp}
                    style="background-color: black; width: 100%; height: 100%"
                ></canvas>
                <div class="map-controls">
                    <button on:click={fitSystemToCanvas}>System View</button>
                    <button on:click={fitPathToView}>Focus Path</button>
                    <button on:click={saveMap}>Save Map</button>
                </div>
            </div>

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
                                on:change={applyVesselPreset}
                            >
                                <option value="">Custom</option>
                                {#each Object.keys(vesselPresets) as preset}
                                    <option value={preset}>{preset}</option>
                                {/each}
                            </select>
                        </div>

                        <div class="form-group">
                            <label for="delta-v">Delta-V (m/s)</label>
                            <input
                                id="delta-v"
                                type="number"
                                bind:value={deltaV}
                                min="0"
                            />
                        </div>

                        <div class="form-group">
                            <label for="mass">Mass (t)</label>
                            <input
                                id="mass"
                                type="number"
                                bind:value={massT}
                                min="0"
                            />
                        </div>

                        <div class="form-group">
                            <label for="thrust">Thrust (N)</label>
                            <input
                                id="thrust"
                                type="number"
                                bind:value={thrustN}
                                min="0"
                            />
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
                                bind:value={timeWeight}
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
                                bind:value={costWeight}
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
                                bind:value={comfortWeight}
                                step="0.1"
                            />
                        </div>

                        <div class="form-group">
                            <label
                                ><input
                                    type="checkbox"
                                    bind:checked={disableCoast}
                                /> Disable Coasting</label
                            >
                        </div>
                    </div>

                    <!-- Object tools -->
                    <div class="option-card">
                        <h4>Object Tools</h4>

                        <div class="form-group">
                            <label for="selected-object">Select Object</label>
                            <select
                                id="selected-object"
                                bind:value={selectedObject}
                            >
                                <option value="">Select...</option>
                                {#each Object.keys(lastPlanetData) as planet}
                                    <option value={planet}>{planet}</option>
                                {/each}
                            </select>
                        </div>

                        <div class="form-group button-group">
                            <button
                                on:click={showTransitMenu}
                                disabled={!selectedObject}
                                >Transit Setting</button
                            >
                            <button
                                on:click={focusOnPlanet}
                                disabled={!selectedObject}
                                >Focus On Object</button
                            >
                        </div>
                    </div>

                    <!-- Settings block -->
                    <div class="option-card">
                        <h4>Settings</h4>
                        <div class="form-group">
                            <label for="launch-time">Time</label>
                            <input
                                id="launch-time"
                                type="string"
                                bind:value={launchTimeInput}
                            />
                            <button
                                class="form-button"
                                on:click={applyLaunchTime}>Apply</button
                            >
                        </div>

                        <div class="form-group">
                            <label for="launch-time">Transit</label>
                            <button on:click={calculatePath}>Calculate</button>
                            <button on:click={clearPath}>Clear</button>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <div class="right-panel">
            <div class="trip-summary">
                <h3>Transit Summary</h3>
                {#if pathResult?.summary}
                    <div class="trip-summary-row">
                        <span class="label">Distance</span>
                        <span class="divider">—</span>
                        <span
                            ><span class="value"
                                >{pathResult.summary.total_distance_au.toFixed(
                                    2,
                                )}</span
                            > <span class="unit">AU</span></span
                        >
                    </div>
                    <div class="trip-summary-row">
                        <span class="label">Travel Time</span>
                        <span class="divider">—</span>
                        <span
                            ><span class="value"
                                >{pathResult.summary.total_time_days.toFixed(
                                    2,
                                )}</span
                            > <span class="unit">d</span></span
                        >
                    </div>
                    <div class="trip-summary-row">
                        <span class="label">Delta-V Cost</span>
                        <span class="divider">—</span>
                        <span
                            ><span class="value"
                                >{pathResult.summary.total_delta_v_km_s.toFixed(
                                    1,
                                )}</span
                            > <span class="unit">km/s</span></span
                        >
                    </div>
                    <div class="trip-summary-row">
                        <span class="label">Avg. Acceleration</span>
                        <span class="divider">—</span>
                        <span
                            ><span class="value"
                                >{pathResult.summary.average_acceleration_g.toFixed(
                                    2,
                                )}</span
                            > <span class="unit">g</span></span
                        >
                    </div>
                {:else}
                    <div>No transit data.</div>
                {/if}
            </div>

            <div class="trip-flow">
                <h4>Transit Flow</h4>
                {#if pathResult?.legs}
                    <div class="trip-card">
                        <div class="trip-card-header">
                            <div class="leg-index-name">
                                <div class="leg-title">
                                    0: {pathResult.origin}
                                </div>
                                <div class="leg-distance">Launch</div>
                            </div>
                            <div class="vertical-divider"></div>
                            <div class="leg-details">
                                <div class="leg-detail-row">
                                    <span class="label">t₀</span>
                                    <span class="divider">—</span>
                                    <span class="value">{launcTimeDisplay}</span
                                    >
                                </div>
                            </div>
                        </div>
                    </div>

                    {#each pathResult.legs as leg, index}
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
                                                <span class="value"
                                                    >{(
                                                        leg.burn_time / 3600
                                                    ).toFixed(1)}</span
                                                > <span class="unit">+</span>
                                                <span class="value"
                                                    >{(
                                                        leg.coast_time / 3600
                                                    ).toFixed(1)}</span
                                                > <span class="unit">hrs</span>
                                                (<span class="value"
                                                    >{(
                                                        leg.total_time / 86400
                                                    ).toFixed(2)}</span
                                                > <span class="unit">d</span>)
                                            </span>
                                        </div>
                                        <div class="leg-detail-row">
                                            <span class="label">a</span>
                                            <span class="divider">—</span>
                                            <span
                                                ><span class="value"
                                                    >{leg.accel_g.toFixed(
                                                        2,
                                                    )}</span
                                                >
                                                <span class="unit">g</span
                                                ></span
                                            >
                                        </div>
                                        <div class="leg-detail-row">
                                            <span class="label">Δv</span>
                                            <span class="divider">—</span>
                                            <span
                                                ><span class="value"
                                                    >{(
                                                        leg.dv_cost / 1000
                                                    ).toFixed(1)}</span
                                                >
                                                <span class="unit">km/s</span
                                                ></span
                                            >
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    {/each}
                {:else}
                    <div>
                        Have you tried <span style="color: #8fa9b5;"
                            >{getRandomObject()}</span
                        >
                        -&gt
                        <span style="color: #8fa9b5;">{getRandomObject()}?</span
                        >
                    </div>
                {/if}
            </div>
        </div>
    </div>
    {#if showContextMenu}
        <div
            class="context-menu"
            style="top: {contextMenuY}px; left: {contextMenuX}px;"
        >
            {#if contextTarget === "planet" && clickedPlanet}
                <div
                    role="button"
                    tabindex="0"
                    on:keypress={handleKey}
                    class="context-option"
                    on:click={() => {
                        selectedObject = clickedPlanet || "";
                        focusOnPlanet();
                        showContextMenu = false;
                    }}
                >
                    Focus
                </div>
                <div
                    role="button"
                    tabindex="0"
                    on:keypress={handleKey}
                    class="context-option"
                    on:click={() => selectPlanet("origin")}
                >
                    Set as Origin
                </div>
                <div
                    role="button"
                    tabindex="0"
                    on:keypress={handleKey}
                    class="context-option"
                    on:click={() => selectPlanet("destination")}
                >
                    Set as Destination
                </div>
                <div
                    role="button"
                    tabindex="0"
                    on:keypress={handleKey}
                    class="context-option"
                    on:click={() => selectPlanet("waypoint")}
                >
                    Add as Waypoint
                </div>
                <div
                    role="button"
                    tabindex="0"
                    on:keypress={handleKey}
                    class="context-option"
                    on:click={() => {
                        removeFromRoute(clickedPlanet);
                        showContextMenu = false;
                    }}
                >
                    Remove from Route
                </div>
            {:else if contextTarget === "map"}
                <div
                    role="button"
                    tabindex="0"
                    on:keypress={handleKey}
                    class="context-option"
                    on:click={() => {
                        origin = "";
                        destination = "";
                        waypoints = [];
                        showContextMenu = false;
                        drawAll();
                        saveState();
                    }}
                >
                    Clear Selection
                </div>
            {/if}
        </div>
    {/if}
</div>

<style>
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

    .canvas-container {
        flex: 1 1 auto;
        overflow: hidden;
    }

    .controls-container {
        flex: 0 0 auto;
        padding: 10px;
        background-color: #111;
        color: white;
    }

    .right-panel {
        flex: 1;
        padding: 10px;
        background-color: #1a1a1a;
        color: white;
        display: flex;
        flex-direction: column;
    }

    .trip-summary {
        margin-bottom: 20px;
    }

    .trip-flow {
        flex: 1;
        overflow-y: auto;
        border-top: 2px solid #333;
        padding-top: 10px;
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

    .page-layout {
        display: flex;
        flex-direction: column;
        height: 100vh;
        width: 100vw;
        overflow: hidden;
        font-family: "Inter";
    }

    .clock-panel {
        background-color: #1a1a1a;
        color: white;
        padding: 10px;
        min-height: 15vh;
        border-bottom: 2px solid #333;
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

    .canvas-container {
        position: relative;
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
        .page-layout {
            flex-direction: row;
        }

        .clock-panel {
            height: 100vh;
            flex-shrink: 0;
        }

        .main-container {
            flex: 1;
            display: flex;
            width: auto;
        }

        .canvas-container {
            flex: 1 1 auto;
            overflow: hidden;
            display: flex;
            align-items: center;
            justify-content: center;
        }

        .clock-container {
            flex-direction: column;
        }
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

    .clock-panel {
        padding: 1rem;
        background: #111;
        color: #eee;
        font-family: "Consolas", "Courier New", monospace;
        border-right: 1px solid #333;
        min-width: 200px;
        box-sizing: border-box;
    }

    .clock-container {
        display: flex;
        flex-wrap: wrap;
        gap: 1.2rem;
        justify-content: center;
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
