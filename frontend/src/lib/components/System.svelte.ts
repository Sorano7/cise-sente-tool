import { getContext, setContext } from "svelte";
import { SvelteMap } from "svelte/reactivity";

export const TIMESTAMP_OFFSET = 23164249536;

/* -- API Endpoints -- */
export const API_BASE = "http://localhost:8001/api";
export const API_ORBITS = "/orbit_data.json";
export const API_BELTS = "/asteroid_belts.json";
export const API_OBJECTS = `${API_BASE}/objects`;
export const API_PATH_FIND = `${API_BASE}/pathfind`;
export const API_VESSELS = `${API_BASE}/vessels`;
export const API_CLOCK = `${API_BASE}/datetime`;

interface ObjectData {
  x: number;
  y: number;
  z?: number;
  type: string;
  a: number;
}

interface Path {
  origin: string;
  destination: string;
  waypoints: string[];
  launchTimeUnix: number;
}

interface PathResult {
  origin: string;
  launchTime: number;
  legs: Record<string, any>[];
  summary: Record<string, any>;
}

export async function loadData(url: string) {
  try {
    const res = await fetch(url);
    if (!res.ok) throw new Error("Fetch failed");
    return await res.json();
  } catch (error) {
    console.error(`Failed to fetch ${url}: ${error}`);
  }
}

interface VesselConfig {
  deltaV: number;
  massT: number;
  thrustN: number;
}

interface Policy {
  timeWeight: number;
  costWeight: number;
  comfortWeight: number;
  disableCoast: boolean;
}

export class SystemState {
  timestamp = $state(Date.now() / 1000 + TIMESTAMP_OFFSET);
  path: Path = $state({ origin: "", destination: "", waypoints: [], launchTimeUnix: this.getUnixTimestamp() });
  pathResult: PathResult | null = $state(null);
  allObjects: Record<string, ObjectData> = $state({})

  vesselConfig: VesselConfig = $state({ deltaV: 3300000, massT: 250, thrustN: 1780000 });
  policy: Policy = $state({ timeWeight: 1, costWeight: 1, comfortWeight: 1, disableCoast: false });

  arrivalPositions: SvelteMap<string, { x: number; y: number }> = new SvelteMap();

  vesselPresets: Record<
    string,
    { delta_v: number; mass_t: number; thrust_n: number }
  > = {};

  needMapRedraw = $state(false);
  focusOnObject = $state(false);
  showContextMenu = $state(false);
  selectedObject: string | null = $state(null);

  constructor() {}

  /**
   * Fetch vessel presets from API and update `this.vesselPresets`
   */
  async updateVesselPresets() {
    this.vesselPresets = await loadData(`${API_VESSELS}/presets`);
  }

  /**
   * Apply preset to `this.vesselConfig`
   * @param presetName 
   */
  applyVesselPreset(presetName: string) {
    if (presetName && this.vesselPresets[presetName]) {
      const preset = this.vesselPresets[presetName];
      this.vesselConfig.deltaV = preset.delta_v;
      this.vesselConfig.massT = preset.mass_t;
      this.vesselConfig.thrustN = preset.thrust_n;
    }
  }

  /**
   * Convert `this.timestamp` to unix timestamp
   * @returns 
   */
  getUnixTimestamp() {
    return this.timestamp - TIMESTAMP_OFFSET;
  }

  /**
   * Update `this.allObjects` positions
   * @param timestamp timestamp to use. Default to current time.
   */
  async updateObjectPositions(timestamp = this.getUnixTimestamp()) {
    this.allObjects = await loadData(`${API_OBJECTS}/positions?timestamp=${timestamp}`);
    this.needMapRedraw = true;
  }

  /**
   * Post a path find request to API
   * @modifies `this.pathResult` 
   */
  async calculatePath() {
    if (!this.path.origin || !this.path.destination) return;
    console.log(`Calculating path for ${this.path.origin} -> ${this.path.destination}`);

    const requestData = {
      vessel: {
        delta_v: this.vesselConfig.deltaV,
        mass_t: this.vesselConfig.massT,
        thrust_n: this.vesselConfig.thrustN,
      },
      policy: {
        time_weight: this.policy.timeWeight,
        cost_weight: this.policy.costWeight,
        comfort_weight: this.policy.comfortWeight,
        disable_coast: this.policy.disableCoast,
      },
      origin: this.path.origin,
      destination: this.path.destination,
      mandatory_stops: $state.snapshot(this.path.waypoints),
      launch_time: this.path.launchTimeUnix,
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

      this.pathResult = await response.json();
      this.needMapRedraw = true;
    } catch (error) {
      console.error("Pathfinding error:", error);
      alert("Failed to calculate path.");
    }
  }

  /**
   * Whether this state has a valid path ready for calculation
   * @returns 
   */
  hasValidPath(): boolean {
    if (!this.pathResult || !this.pathResult.legs || this.pathResult.legs.length === 0) return false;
    return true;
  }

  /**
   * Update `this.arrivalPositions` by fetching position at the given timestamp or retrieve if already exists.
   * @param name 
   * @param timestamp 
   * @returns 
   */
  async getArrivalPosition(name: string, timestamp: number) {
    const key = `${name}_${timestamp}`;

    if (!this.arrivalPositions.has(key)) {
      const pos = await fetchPositionAtTime(name, timestamp);
      if (pos) this.arrivalPositions.set(key, { x: pos.x, y: pos.y });
    };

    return this.arrivalPositions.get(key)
  }

  AddObjectToPath(name: string, type: "origin" | "destination" | "waypoint") {
    switch (type) {
      case "origin":
        if (name === this.path.destination) this.path.destination = "";
        this.path.waypoints = this.path.waypoints.filter((p) => p !== name);
        this.path.origin = name;
        break;

      case "destination":
        if (name === this.path.origin) this.path.origin = "";
        this.path.waypoints = this.path.waypoints.filter((p) => p !== name);
        this.path.destination = name;
        break;

      case "waypoint":
        if (name === this.path.origin) this.path.origin = "";
        if (name === this.path.destination) this.path.destination = "";
        if (!this.path.waypoints.includes(name)) {
          this.path.waypoints = [...this.path.waypoints, name];
        }
    }
  }

  AddWaypoint(name: string) {
    if (
      !this.path.waypoints.includes(name) &&
      name !== this.path.origin &&
      name !== this.path.destination
    ) {
      this.path.waypoints = [...this.path.waypoints, name];
    }
  }

  RemoveWaypointByIndex(index: number) {
    this.path.waypoints = this.path.waypoints.filter((_, i) => i !== index);
  }

  RemoveObjectFromPath(name: string) {
    if (name === this.path.origin) {
      this.path.origin = "";
    } else if (name === this.path.destination) {
      this.path.destination = "";
    } else {
      const index = this.path.waypoints.indexOf(name);
      if (index !== -1) {
        this.RemoveWaypointByIndex(index);
      }
    }
  }

  clearPath() {
    this.path = {
      origin: "",
      destination: "",
      waypoints: [],
      launchTimeUnix: this.getUnixTimestamp()
    }
    this.pathResult = null;
    this.arrivalPositions.clear();
    this.needMapRedraw = true;
    console.log(this.arrivalPositions);
  }

  isValidObject(name: string) {
    if (!this.allObjects[name]) return false;
    return true;
  }

  getObjectByName(name: string) {
    return this.allObjects[name];
  }

  async applyTimeString(time: string) {
    if (time === "") time = this.getUnixTimestamp().toString();   
    const data = await loadData(`${API_CLOCK}/parse?input=${encodeURIComponent(time)}`);

    if (data.unix_timestamp) {
      this.path.launchTimeUnix = parseFloat(data.unix_timestamp);
      console.log(this.timestamp - TIMESTAMP_OFFSET);
      console.log(this.path.launchTimeUnix);
      this.updateObjectPositions(this.path.launchTimeUnix);
      this.needMapRedraw = true;
    }
  }
}

const SYSTEM_KEY = Symbol('System');

export function setSystemState() {
  return setContext(SYSTEM_KEY, new SystemState());
}

export function getSystemState() {
  return getContext<ReturnType<typeof setSystemState>>(SYSTEM_KEY);
}

/**
 * Fetch position of an object at the given time
 *
 * @param name
 * @param timestamp
 */
export async function fetchPositionAtTime(name: string, timestamp: number) {
  try {
    const res = await fetch(
      `${API_OBJECTS}/position?name=${encodeURIComponent(name)}&timestamp=${timestamp}`,
    );
    if (!res.ok) {
      console.error(
        `[fetchPositionAtTime] Fetch failed for ${name} at ${timestamp}:`,
        res.statusText,
      );
      return null;
    }

    const data = await res.json();
    return data;
  } catch (err) {
    console.error(
      `[fetchPositionAtTime] Error for ${name} at ${timestamp}:`,
      err,
    );
    return null;
  }
}