export const API_BASE = "http://localhost:8001/api";

export const API_ORBITS = "/orbit_data.json";
export const API_BELTS = "/asteroid_belts.json";
export const API_OBJECTS = `${API_BASE}/objects`;

export const API_PATH_FIND = `${API_BASE}/pathfind`;
export const API_VESSELS = `${API_BASE}/vessels`;

export const API_CLOCK = `${API_BASE}/datetime`;

export const API_LANGUAGE = `${API_BASE}/language`;

export async function loadData(url: string) {
  try {
    const res = await fetch(url);
    if (!res.ok) throw new Error("Fetch failed");
    return await res.json();
  } catch (error) {
    console.error(`Failed to fetch ${url}: ${error}`);
  }
}