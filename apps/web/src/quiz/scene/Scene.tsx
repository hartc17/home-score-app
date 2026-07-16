import type { JSX } from "react";
import { NEUTRAL, palette, type Palette } from "./tokens.ts";
import { sceneId, type SceneSpec } from "./spec.ts";

// Parametric flat-illustration renderer. One fixed geometry per base room; tone
// swaps the palette, era swaps the motif set, and the two poles of any pair
// therefore differ only on the axis under test. Perspective, line weight, and
// shadow style are fixed across the whole set (illustration-kit v2, section 4).

const W = 400;
const H = 300;
const FLOOR_Y = 206;
const STROKE = NEUTRAL.ink;
const LW = 2.4;

interface Theme {
  c: Palette;
  traditional: boolean;
  colorWall: boolean;
  engineered: boolean;
}

function resolve(spec: SceneSpec): Theme {
  return {
    c: palette(spec.tone),
    traditional: spec.era === "traditional",
    colorWall: (spec.wall ?? "light") === "color",
    engineered: (spec.material ?? "natural") === "engineered",
  };
}

function line(x1: number, y1: number, x2: number, y2: number, w = LW, color = STROKE) {
  return <line x1={x1} y1={y1} x2={x2} y2={y2} stroke={color} strokeWidth={w} strokeLinecap="round" />;
}

// Horizontal wood grain, drawn only for natural material; engineered surfaces
// stay flat and instead take a faint gloss highlight.
function surface(x: number, y: number, w: number, h: number, fill: string, t: Theme, rx = 0) {
  const rows: JSX.Element[] = [];
  if (!t.engineered) {
    for (let i = 1; i <= Math.floor(h / 12); i++) {
      rows.push(
        <line
          key={i}
          x1={x + 4}
          y1={y + i * 12}
          x2={x + w - 4}
          y2={y + i * 12}
          stroke={STROKE}
          strokeWidth={0.6}
          opacity={0.25}
        />,
      );
    }
  }
  return (
    <>
      <rect x={x} y={y} width={w} height={h} rx={rx} fill={fill} stroke={STROKE} strokeWidth={LW} />
      {t.engineered && <rect x={x + 3} y={y + 3} width={w - 6} height={Math.max(3, h * 0.22)} rx={rx} fill="#ffffff" opacity={0.14} />}
      {rows}
    </>
  );
}

function windowEl(t: Theme, x: number, y: number, w: number, h: number) {
  const { c } = t;
  if (t.traditional) {
    return (
      <g>
        <rect x={x - 6} y={y - 8} width={w + 12} height={8} fill={c.wood2} stroke={STROKE} strokeWidth={LW} />
        <rect x={x} y={y} width={w} height={h} fill={NEUTRAL.glass} stroke={STROKE} strokeWidth={LW} />
        {line(x + w / 2, y, x + w / 2, y + h)}
        {line(x, y + h / 2, x + w, y + h / 2)}
        <rect x={x - 6} y={y + h} width={w + 12} height={7} fill={c.wood2} stroke={STROKE} strokeWidth={LW} />
      </g>
    );
  }
  return (
    <g>
      <rect x={x} y={y - 10} width={w} height={h + 12} fill={NEUTRAL.glass} stroke={STROKE} strokeWidth={LW} />
    </g>
  );
}

function shell(t: Theme, opts: { window?: [number, number, number, number] } = {}) {
  const { c } = t;
  const wallFill = c.wall;
  return (
    <>
      <rect x={0} y={0} width={W} height={FLOOR_Y} fill={wallFill} />
      {t.colorWall && <rect x={0} y={0} width={W} height={FLOOR_Y} fill={c.accent} opacity={0.42} />}
      {t.traditional && <rect x={0} y={12} width={W} height={10} fill={c.wall} stroke={STROKE} strokeWidth={LW} opacity={0.9} />}
      {t.traditional && (
        <>
          {line(0, 150, W, 150, 1.4)}
          <rect x={20} y={158} width={64} height={40} fill="none" stroke={STROKE} strokeWidth={1.4} opacity={0.6} />
          <rect x={96} y={158} width={64} height={40} fill="none" stroke={STROKE} strokeWidth={1.4} opacity={0.6} />
        </>
      )}
      <rect x={0} y={FLOOR_Y} width={W} height={H - FLOOR_Y} fill={c.floor} />
      {!t.engineered &&
        [0, 1, 2, 3, 4, 5, 6].map((i) => (
          <line key={i} x1={0} y1={FLOOR_Y + 8 + i * 13} x2={W} y2={FLOOR_Y + 8 + i * 13} stroke={STROKE} strokeWidth={0.5} opacity={0.18} />
        ))}
      {line(0, FLOOR_Y, W, FLOOR_Y, LW)}
      <rect x={0} y={FLOOR_Y - 8} width={W} height={8} fill={c.wall} stroke={STROKE} strokeWidth={LW} />
      {opts.window && windowEl(t, ...opts.window)}
    </>
  );
}

function shadow(cx: number, cy: number, rx: number) {
  return <ellipse cx={cx} cy={cy} rx={rx} ry={6} fill={NEUTRAL.shadow} />;
}

function art(t: Theme, x: number, y: number) {
  const { c } = t;
  if (t.traditional) {
    return (
      <g>
        {[0, 1, 2].map((i) => (
          <rect
            key={i}
            x={x + (i % 3) * 30}
            y={y + (i === 1 ? 10 : 0)}
            width={24}
            height={30}
            fill={c.wall}
            stroke={c.metal}
            strokeWidth={2.4}
          />
        ))}
      </g>
    );
  }
  return <rect x={x} y={y} width={70} height={46} fill={c.wall} stroke={STROKE} strokeWidth={LW} />;
}

function plant(t: Theme, x: number, y: number) {
  return (
    <g>
      <rect x={x} y={y} width={20} height={22} rx={2} fill={t.c.feature} stroke={STROKE} strokeWidth={LW} />
      <path d={`M${x + 10} ${y} C ${x - 4} ${y - 26}, ${x + 2} ${y - 30}, ${x + 10} ${y - 14} C ${x + 18} ${y - 30}, ${x + 24} ${y - 26}, ${x + 10} ${y} Z`} fill={NEUTRAL.green1} stroke={STROKE} strokeWidth={LW} />
      <path d={`M${x + 10} ${y - 6} C ${x + 4} ${y - 22}, ${x + 8} ${y - 26}, ${x + 12} ${y - 18}`} fill={NEUTRAL.green2} stroke={STROKE} strokeWidth={1.2} />
    </g>
  );
}

function renderLiving(t: Theme) {
  const { c } = t;
  const sofaY = 150;
  return (
    <>
      {shell(t, { window: [286, 66, 92, 96] })}
      {art(t, t.traditional ? 40 : 44, 70)}
      {plant(t, 356, 184)}
      {shadow(150, 208, 120)}
      {/* sofa */}
      {t.traditional ? (
        <g>
          <rect x={54} y={sofaY} width={168} height={54} rx={10} fill={c.primary} stroke={STROKE} strokeWidth={LW} />
          <rect x={44} y={sofaY - 6} width={26} height={60} rx={12} fill={c.primary} stroke={STROKE} strokeWidth={LW} />
          <rect x={206} y={sofaY - 6} width={26} height={60} rx={12} fill={c.primary} stroke={STROKE} strokeWidth={LW} />
          {[80, 118, 156, 194].map((x) => (
            <circle key={x} cx={x} cy={sofaY + 20} r={2.4} fill={STROKE} opacity={0.5} />
          ))}
        </g>
      ) : (
        <g>
          {surface(48, sofaY + 8, 184, 40, c.primary, t, 4)}
          <rect x={48} y={sofaY - 6} width={184} height={20} rx={4} fill={c.primary} stroke={STROKE} strokeWidth={LW} />
        </g>
      )}
      {/* coffee table */}
      {t.traditional ? (
        <g>
          {surface(96, 176, 92, 16, c.wood2, t, 2)}
          {line(104, 192, 104, 204)}
          {line(180, 192, 180, 204)}
        </g>
      ) : (
        <g>
          {surface(100, 180, 88, 12, c.wood2, t, 2)}
          <rect x={104} y={192} width={80} height={4} fill={c.metal} stroke={STROKE} strokeWidth={1.4} />
        </g>
      )}
      {/* rug */}
      <ellipse cx={150} cy={230} rx={140} ry={22} fill={c.accent} opacity={t.traditional ? 0.5 : 0.3} />
      {t.traditional && <ellipse cx={150} cy={230} rx={120} ry={17} fill="none" stroke={c.metal} strokeWidth={2} opacity={0.7} />}
    </>
  );
}

function renderKitchen(t: Theme) {
  const { c } = t;
  const counterY = 150;
  return (
    <>
      {shell(t, { window: [292, 60, 86, 76] })}
      {/* backsplash */}
      {t.traditional
        ? [0, 1, 2, 3, 4, 5].map((i) => (
            <rect key={i} x={30 + i * 40} y={120} width={38} height={16} fill={c.wall} stroke={c.metal} strokeWidth={1.2} opacity={0.8} />
          ))
        : <rect x={30} y={120} width={236} height={20} fill={c.feature} opacity={0.5} />}
      {/* hood */}
      {t.traditional ? (
        <path d={`M120 60 L200 60 L188 96 L132 96 Z`} fill={c.metal} stroke={STROKE} strokeWidth={LW} />
      ) : (
        <rect x={132} y={70} width={56} height={12} fill={c.metal} stroke={STROKE} strokeWidth={LW} />
      )}
      {shadow(150, 208, 130)}
      {/* base cabinets */}
      {surface(30, counterY, 236, 8, c.wood2, t)}
      <rect x={30} y={counterY + 8} width={236} height={48} fill={c.primary} stroke={STROKE} strokeWidth={LW} />
      {[30, 89, 148, 207].map((x) => (
        <g key={x}>
          <rect x={x + 4} y={counterY + 12} width={51} height={40} fill="none" stroke={STROKE} strokeWidth={t.traditional ? 1.8 : 0.8} opacity={t.traditional ? 0.9 : 0.4} />
          {t.traditional ? (
            <circle cx={x + 46} cy={counterY + 32} r={2.6} fill={c.metal} stroke={STROKE} strokeWidth={1} />
          ) : (
            <line x1={x + 46} y1={counterY + 16} x2={x + 46} y2={counterY + 30} stroke={c.metal} strokeWidth={2.4} />
          )}
        </g>
      ))}
      {/* island */}
      {surface(150, 182, 120, 8, c.wood2, t)}
      <rect x={158} y={190} width={104} height={40} fill={c.primary} stroke={STROKE} strokeWidth={LW} />
      {!t.traditional && <rect x={150} y={182} width={10} height={54} fill={c.wood2} stroke={STROKE} strokeWidth={LW} />}
      {t.traditional && <rect x={62} y={126} width={44} height={10} fill={c.wood2} stroke={STROKE} strokeWidth={LW} />}
    </>
  );
}

function renderBedroom(t: Theme) {
  const { c } = t;
  const bedY = 150;
  return (
    <>
      {shell(t, { window: [300, 66, 78, 84] })}
      {/* pendant / lamp */}
      {t.traditional ? (
        <g>
          {line(70, 100, 70, 118)}
          <path d="M56 118 L84 118 L80 134 L60 134 Z" fill={c.metal} stroke={STROKE} strokeWidth={LW} />
        </g>
      ) : (
        <g>
          {line(70, 66, 70, 108)}
          <circle cx={70} cy={112} r={7} fill={c.metal} stroke={STROKE} strokeWidth={LW} />
        </g>
      )}
      {art(t, t.traditional ? 108 : 120, 74)}
      {shadow(180, 210, 150)}
      {/* headboard */}
      {t.traditional ? (
        <rect x={70} y={120} width={190} height={44} rx={8} fill={c.primary} stroke={STROKE} strokeWidth={LW} />
      ) : (
        <rect x={70} y={140} width={190} height={22} rx={3} fill={c.primary} stroke={STROKE} strokeWidth={LW} />
      )}
      {t.traditional && [110, 150, 190, 230].map((x) => <circle key={x} cx={x} cy={140} r={2.4} fill={STROKE} opacity={0.5} />)}
      {/* mattress + bedding */}
      {surface(60, bedY + 14, 214, 40, c.wall, t, 6)}
      <rect x={60} y={bedY + 14} width={214} height={16} rx={6} fill={c.accent} opacity={t.traditional ? 0.5 : 0.32} stroke={STROKE} strokeWidth={LW} />
      {/* nightstand */}
      {t.traditional ? (
        <g>
          <rect x={286} y={176} width={40} height={30} fill={c.wood2} stroke={STROKE} strokeWidth={LW} />
          {line(292, 206, 292, 220)}
          {line(320, 206, 320, 220)}
          <circle cx={306} cy={191} r={2.4} fill={c.metal} stroke={STROKE} strokeWidth={1} />
        </g>
      ) : (
        <rect x={286} y={182} width={42} height={22} fill={c.wood2} stroke={STROKE} strokeWidth={LW} />
      )}
    </>
  );
}

function renderWalls(t: Theme) {
  const { c } = t;
  return (
    <>
      {shell(t)}
      {shadow(200, 210, 120)}
      {t.traditional ? (
        <g>
          {/* wainscot */}
          <rect x={0} y={120} width={W} height={86} fill="none" stroke={STROKE} strokeWidth={1.4} opacity={0.5} />
          {[40, 130, 220, 310].map((x) => (
            <rect key={x} x={x} y={130} width={60} height={66} fill="none" stroke={STROKE} strokeWidth={1.4} opacity={0.5} />
          ))}
          {/* salon-style art cluster */}
          {[
            [120, 46, 44, 34],
            [176, 40, 48, 40],
            [236, 50, 40, 30],
            [130, 90, 40, 26],
            [186, 88, 34, 30],
          ].map(([x, y, w, h], i) => (
            <rect key={i} x={x} y={y} width={w} height={h} fill={c.wall} stroke={c.metal} strokeWidth={2.4} />
          ))}
          {/* turned-leg console */}
          {surface(150, 160, 100, 12, c.wood2, t, 2)}
          {line(160, 172, 160, 200, 3)}
          {line(240, 172, 240, 200, 3)}
          <circle cx={160} cy={180} r={3} fill={c.wood2} stroke={STROKE} strokeWidth={1.4} />
          <circle cx={240} cy={180} r={3} fill={c.wood2} stroke={STROKE} strokeWidth={1.4} />
          {plant(t, 226, 158)}
        </g>
      ) : (
        <g>
          {/* single centered large artwork, negative space */}
          <rect x={150} y={54} width={100} height={74} fill={c.wall} stroke={STROKE} strokeWidth={LW} />
          <rect x={166} y={70} width={68} height={42} fill={c.accent} opacity={0.5} />
          {/* minimal bench */}
          {surface(150, 176, 100, 10, c.wood2, t, 2)}
          <rect x={158} y={186} width={6} height={18} fill={c.metal} />
          <rect x={236} y={186} width={6} height={18} fill={c.metal} />
        </g>
      )}
    </>
  );
}

function sky(t: Theme, ground: string, horizon = 168) {
  return (
    <>
      <rect x={0} y={0} width={W} height={horizon} fill={NEUTRAL.sky} />
      <rect x={0} y={horizon} width={W} height={H - horizon} fill={ground} />
      {!t.engineered &&
        [0, 1, 2, 3].map((i) => (
          <line key={i} x1={0} y1={horizon + 14 + i * 24} x2={W} y2={horizon + 14 + i * 24} stroke={STROKE} strokeWidth={0.5} opacity={0.12} />
        ))}
    </>
  );
}

function flame(x: number, y: number, accent: string, s = 1) {
  const h = 40 * s;
  const w = 13 * s;
  return (
    <g>
      <path
        d={`M${x} ${y} C ${x - w} ${y - h * 0.55}, ${x + w * 0.5} ${y - h * 0.65}, ${x} ${y - h} C ${x + w * 1.1} ${y - h * 0.6}, ${x + w} ${y - h * 0.2}, ${x} ${y} Z`}
        fill={accent}
        stroke={STROKE}
        strokeWidth={LW}
      />
      <path d={`M${x} ${y - h * 0.15} C ${x - w * 0.4} ${y - h * 0.45}, ${x + w * 0.25} ${y - h * 0.5}, ${x} ${y - h * 0.7}`} fill="#ffffff" opacity={0.25} />
    </g>
  );
}

function renderFacade(t: Theme) {
  const { c } = t;
  return (
    <>
      {sky(t, "#B7B2A6")}
      {shadow(200, 250, 150)}
      {/* house mass */}
      <rect x={70} y={110} width={260} height={110} fill={t.colorWall ? c.accent : c.feature} stroke={STROKE} strokeWidth={LW} opacity={t.colorWall ? 0.7 : 1} />
      {!t.engineered && [0, 1, 2, 3, 4].map((i) => <line key={i} x1={70} y1={128 + i * 20} x2={330} y2={128 + i * 20} stroke={STROKE} strokeWidth={0.5} opacity={0.2} />)}
      {t.traditional ? (
        <g>
          {/* gable roof + chimney */}
          <polygon points="60,112 200,50 340,112" fill={c.wood2} stroke={STROKE} strokeWidth={LW} />
          <rect x={280} y={66} width={22} height={40} fill={c.feature} stroke={STROKE} strokeWidth={LW} />
          {/* symmetrical shuttered windows */}
          {[110, 250].map((x) => (
            <g key={x}>
              <rect x={x} y={134} width={44} height={48} fill={NEUTRAL.glass} stroke={STROKE} strokeWidth={LW} />
              {line(x + 22, 134, x + 22, 182, 1.6)}
              {line(x, 158, x + 44, 158, 1.6)}
              <rect x={x - 10} y={134} width={9} height={48} fill={c.primary} stroke={STROKE} strokeWidth={1.6} />
              <rect x={x + 45} y={134} width={9} height={48} fill={c.primary} stroke={STROKE} strokeWidth={1.6} />
            </g>
          ))}
          {/* porch + door */}
          <rect x={176} y={150} width={48} height={70} fill={c.wood2} stroke={STROKE} strokeWidth={LW} />
          {line(170, 150, 230, 150, 4)}
          {line(178, 150, 178, 220, 4)}
          {line(222, 150, 222, 220, 4)}
        </g>
      ) : (
        <g>
          {/* flat roof + asymmetric glazing + canopy */}
          <rect x={64} y={100} width={272} height={12} fill={c.wood2} stroke={STROKE} strokeWidth={LW} />
          <rect x={92} y={128} width={120} height={92} fill={NEUTRAL.glass} stroke={STROKE} strokeWidth={LW} />
          {line(152, 128, 152, 220, 1.6)}
          <rect x={244} y={150} width={40} height={70} fill={c.wood2} stroke={STROKE} strokeWidth={LW} />
          <rect x={236} y={144} width={56} height={8} fill={c.metal} stroke={STROKE} strokeWidth={LW} />
        </g>
      )}
      {plant(t, 44, 216)}
      {plant(t, 344, 216)}
    </>
  );
}

function renderBackyard(t: Theme) {
  const { c } = t;
  const patioY = 178;
  return (
    <>
      {sky(t, NEUTRAL.green1, 120)}
      {/* low planting bed along the lawn/patio line, both poles */}
      {t.traditional ? (
        [24, 52, 80, 300, 330, 360].map((x, i) => (
          <circle key={i} cx={x} cy={patioY - 6} r={20} fill={i < 3 ? NEUTRAL.green2 : NEUTRAL.green1} stroke={STROKE} strokeWidth={LW} />
        ))
      ) : (
        [22, 34, 46, 58, 330, 342, 354, 366].map((x, i) => (
          <path key={i} d={`M${x} ${patioY} C ${x - 9} ${patioY - 34}, ${x + 3} ${patioY - 42}, ${x + 5} ${patioY - 56}`} fill="none" stroke={i % 2 ? NEUTRAL.green1 : NEUTRAL.green2} strokeWidth={3.2} strokeLinecap="round" />
        ))
      )}
      {/* patio (stone pavers) vs deck (composite boards) */}
      {t.traditional ? (
        <g>
          <rect x={0} y={patioY} width={W} height={H - patioY} fill={c.feature} opacity={0.6} />
          {[70, 140, 210, 280, 350].map((x) => <line key={x} x1={x} y1={patioY} x2={x} y2={H} stroke={STROKE} strokeWidth={0.7} opacity={0.28} />)}
          {[patioY + 28, patioY + 64, patioY + 100].map((y) => <line key={y} x1={0} y1={y} x2={W} y2={y} stroke={STROKE} strokeWidth={0.7} opacity={0.28} />)}
        </g>
      ) : (
        surface(0, patioY, W, H - patioY, c.wood2, t)
      )}
      {line(0, patioY, W, patioY, LW)}
      {shadow(150, 260, 96)}
      {shadow(300, 268, 56)}
      {/* seating: bistro set (traditional) vs modular lounge (modern) */}
      {t.traditional ? (
        <g>
          {/* round bistro table + two chairs */}
          <ellipse cx={130} cy={214} rx={34} ry={12} fill={c.metal} stroke={STROKE} strokeWidth={LW} />
          {line(130, 214, 130, 250, 3)}
          {line(116, 250, 144, 250, 3)}
          {[86, 174].map((x) => (
            <g key={x}>
              <rect x={x - 12} y={206} width={24} height={10} rx={3} fill="none" stroke={c.metal} strokeWidth={2.6} />
              <path d={`M${x - 12} 206 L ${x - 12} 190 L ${x + 12} 190`} fill="none" stroke={c.metal} strokeWidth={2.6} />
              {line(x - 8, 216, x - 8, 236, 2.2)}
              {line(x + 8, 216, x + 8, 236, 2.2)}
            </g>
          ))}
        </g>
      ) : (
        <g>
          {/* low modular sofa + coffee block */}
          {surface(60, 214, 150, 34, c.primary, t, 4)}
          <rect x={60} y={200} width={150} height={18} rx={4} fill={c.primary} stroke={STROKE} strokeWidth={LW} />
          <rect x={96} y={214} width={40} height={14} rx={3} fill={c.accent} opacity={0.35} />
          {surface(150, 232, 70, 12, c.wood2, t, 2)}
        </g>
      )}
      {/* fire feature: bowl (traditional) vs linear trough (modern) */}
      {t.traditional ? (
        <g>
          <ellipse cx={300} cy={244} rx={34} ry={13} fill={c.feature} stroke={STROKE} strokeWidth={LW} />
          <ellipse cx={300} cy={240} rx={30} ry={10} fill={STROKE} opacity={0.25} />
          {flame(300, 240, c.accent)}
        </g>
      ) : (
        <g>
          <rect x={256} y={236} width={92} height={16} rx={2} fill={c.feature} stroke={STROKE} strokeWidth={LW} />
          {[280, 302, 324].map((x) => <g key={x}>{flame(x, 240, c.accent, 0.62)}</g>)}
        </g>
      )}
    </>
  );
}

const RENDERERS: Record<SceneSpec["base"], (t: Theme) => JSX.Element> = {
  living: renderLiving,
  kitchen: renderKitchen,
  bedroom: renderBedroom,
  walls: renderWalls,
  facade: renderFacade,
  backyard: renderBackyard,
};

export function Scene({ spec }: { spec: SceneSpec }) {
  const theme = resolve(spec);
  return (
    <svg
      viewBox={`0 0 ${W} ${H}`}
      className="h-full w-full"
      role="img"
      aria-label="room option"
      data-scene={sceneId(spec)}
      preserveAspectRatio="xMidYMid slice"
    >
      {RENDERERS[spec.base](theme)}
    </svg>
  );
}
