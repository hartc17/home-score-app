import type { PlateSpec } from "./questions.ts";

// SVG stand-in for a curated photo. Neutral by construction: both plates in a pair
// share complexity and framing, and differ only along the taste axis being tested.
// Swapping to a real photo bank replaces this component with an <img>.

const WARM = { wall: "#e7d3bd", floor: "#b98a5e", accent: "#c2703d", sky: "#f0dcc4" };
const COOL = { wall: "#d7dee3", floor: "#8f9aa2", accent: "#5b7a8c", sky: "#dbe6ec" };

function palette(spec: PlateSpec) {
  const p = spec.warm ? WARM : COOL;
  return {
    wall: spec.lightWalls ? p.wall : spec.warm ? "#8a5a3c" : "#4d6470",
    floor: p.floor,
    accent: p.accent,
    sky: p.sky,
  };
}

export function Plate({ spec }: { spec: PlateSpec }) {
  const c = palette(spec);
  const trim = spec.ornate ? c.accent : c.wall;

  return (
    <svg viewBox="0 0 200 150" className="h-full w-full" role="img" aria-label="room option">
      <rect x="0" y="0" width="200" height="150" fill={c.wall} />
      {spec.motif === "exterior" || spec.motif === "yard" ? (
        <>
          <rect x="0" y="0" width="200" height="80" fill={c.sky} />
          <rect x="0" y="80" width="200" height="70" fill={spec.motif === "yard" ? "#8ba36b" : c.floor} />
          <polygon points="40,80 100,40 160,80" fill={c.accent} />
          <rect x="60" y="80" width="80" height="55" fill={c.wall} />
          <rect x="90" y="100" width="20" height="35" fill={trim} />
          {spec.ornate && <rect x="66" y="86" width="68" height="4" fill={c.accent} />}
        </>
      ) : (
        <>
          <rect x="0" y="110" width="200" height="40" fill={c.floor} />
          <rect x="150" y="30" width="40" height="80" fill={c.sky} stroke={trim} strokeWidth={spec.ornate ? 4 : 2} />
          {spec.ornate && <line x1="170" y1="30" x2="170" y2="110" stroke={trim} strokeWidth="2" />}
          {spec.motif === "kitchen" && <rect x="16" y="86" width="90" height="24" fill={c.accent} />}
          {spec.motif === "living" && <rect x="24" y="88" width="70" height="22" rx="6" fill={c.accent} />}
          {spec.motif === "bedroom" && <rect x="24" y="84" width="86" height="26" rx="4" fill={c.accent} />}
          {spec.motif === "wall" && <rect x="70" y="40" width="60" height="46" fill={spec.ornate ? c.accent : c.wall} stroke={trim} strokeWidth="3" />}
          {spec.motif === "kitchen" && <rect x="16" y="60" width="90" height="6" fill={trim} />}
        </>
      )}
    </svg>
  );
}
