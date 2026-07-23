import { useState } from "react";
import type { TasteProfile } from "./inference.ts";
import { archetypeCopy } from "./inference.ts";
import { AXES, AXIS_IDS } from "./axes.ts";
import { CATEGORIES, type Category } from "./categories.ts";
import { shareCard } from "./shareCard.ts";

const CATEGORY_LABEL: Record<Category, string> = {
  bones: "Bones",
  warmth: "Warmth",
  finish: "Finish",
  outdoor: "Outdoor",
  value: "Value",
  age: "Age",
};

function bandLabel(band: string): string {
  if (band === "strong") return "clear";
  if (band === "slight") return "slight";
  return "no lean";
}

export function Reveal({
  profile,
  onRetake,
  onAddGates,
  onScoreListings,
}: {
  profile: TasteProfile;
  onRetake: () => void;
  onAddGates: () => void;
  onScoreListings?: () => void;
}) {
  const { rubric, axes } = profile;
  const gates = rubric.gates;
  const [sharing, setSharing] = useState(false);
  const blend = Object.entries(rubric.archetype.blend).sort((a, b) => b[1] - a[1]);

  async function handleShare() {
    setSharing(true);
    try {
      await shareCard(rubric.archetype.name, rubric.archetype.blend);
    } catch {
      // A cancelled share or an unsupported browser is not an error worth surfacing.
    } finally {
      setSharing(false);
    }
  }
  const weights = CATEGORIES.map((c) => ({ cat: c, weight: rubric.category_weights[c] }));
  const maxWeight = Math.max(...weights.map((w) => w.weight));

  return (
    <div className="mx-auto min-h-screen max-w-4xl px-6 py-12">
      <section className="mb-10 rounded-3xl bg-stone-800 px-8 py-12 text-center text-stone-50 shadow-lg">
        <p className="mb-2 text-sm uppercase tracking-widest text-stone-400">Your house flavor</p>
        <h1 className="mb-4 text-4xl font-bold">{rubric.archetype.name}</h1>
        <p className="mx-auto max-w-xl text-lg leading-relaxed text-stone-200">
          {archetypeCopy(rubric.archetype.name)}
        </p>
        <div className="mt-6 flex flex-wrap justify-center gap-2">
          {blend.map(([style, share]) => (
            <span key={style} className="rounded-full bg-stone-700 px-3 py-1 text-sm capitalize text-stone-100">
              {style} {Math.round(share * 100)}%
            </span>
          ))}
        </div>
        <button
          onClick={() => void handleShare()}
          disabled={sharing}
          className="mt-8 inline-flex items-center gap-2 rounded-full bg-stone-50 px-6 py-2.5 text-sm font-medium text-stone-800 transition hover:bg-white disabled:opacity-60"
        >
          {sharing ? "Preparing..." : "Share my flavor"}
        </button>
      </section>

      <section className="grid grid-cols-1 gap-8 md:grid-cols-2">
        <div>
          <h2 className="mb-4 text-sm font-semibold uppercase tracking-wide text-stone-500">Your directions</h2>
          <ul className="space-y-3">
            {AXIS_IDS.map((axis) => {
              const stat = axes[axis];
              const poles = AXES[axis];
              return (
                <li key={axis} className="rounded-xl border border-stone-200 bg-white px-4 py-3">
                  <div className="mb-1 flex items-center justify-between text-sm text-stone-500">
                    <span className="capitalize">{poles.neg.replace(/_/g, " ")}</span>
                    <span className="capitalize">{poles.pos.replace(/_/g, " ")}</span>
                  </div>
                  <div className="relative h-2 rounded-full bg-stone-100" aria-hidden="true">
                    <div
                      className="absolute top-1/2 h-4 w-4 -translate-y-1/2 rounded-full bg-stone-800"
                      style={{ left: `calc(${((stat.signedStrength + 1) / 2) * 100}% - 8px)` }}
                    />
                  </div>
                  <p className="mt-1 text-xs text-stone-400">
                    {stat.direction ? `${stat.direction.replace(/_/g, " ")} (${bandLabel(stat.band)})` : "no lean"}
                  </p>
                </li>
              );
            })}
          </ul>
        </div>

        <div>
          <h2 className="mb-4 text-sm font-semibold uppercase tracking-wide text-stone-500">What you weight</h2>
          <ul className="space-y-3">
            {weights.map(({ cat, weight }) => (
              <li key={cat}>
                <div className="mb-1 flex items-center justify-between text-sm">
                  <span className="text-stone-700">{CATEGORY_LABEL[cat]}</span>
                  <span className="text-stone-500">{weight}</span>
                </div>
                <div className="h-2 rounded-full bg-stone-100" aria-hidden="true">
                  <div className="h-full rounded-full bg-stone-700" style={{ width: `${(weight / maxWeight) * 100}%` }} />
                </div>
              </li>
            ))}
          </ul>
        </div>
      </section>

      <section className="mt-12 rounded-2xl border border-stone-200 bg-white px-6 py-6">
        {gates ? (
          <>
            <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-stone-500">Your must-haves</h2>
            <div className="flex flex-wrap gap-2">
              <span className="rounded-full bg-stone-100 px-3 py-1 text-sm text-stone-700">
                Up to ${gates.budget_max.toLocaleString()}
              </span>
              <span className="rounded-full bg-stone-100 px-3 py-1 text-sm text-stone-700">
                {gates.min_beds}+ bd / {gates.min_baths}+ ba
              </span>
              {gates.districts.length > 0 && (
                <span className="rounded-full bg-stone-100 px-3 py-1 text-sm text-stone-700">
                  {gates.districts.join(", ")}
                </span>
              )}
              {gates.exclude_main_road && (
                <span className="rounded-full bg-stone-100 px-3 py-1 text-sm text-stone-700">No main road</span>
              )}
            </div>
            <button onClick={onAddGates} className="mt-4 text-sm text-stone-500 underline hover:text-stone-700">
              Edit must-haves
            </button>
          </>
        ) : (
          <div className="flex flex-col items-center gap-3 text-center sm:flex-row sm:justify-between sm:text-left">
            <p className="text-stone-700">
              House-hunting for real? Add your must-haves so we can score listings against your taste.
            </p>
            <button
              onClick={onAddGates}
              className="whitespace-nowrap rounded-full bg-stone-800 px-5 py-2.5 text-sm font-medium text-white transition hover:bg-stone-700"
            >
              Add must-haves
            </button>
          </div>
        )}
      </section>

      <div className="mt-8 flex items-center justify-center gap-3">
        {onScoreListings && (
          <button
            onClick={onScoreListings}
            className="rounded-full bg-stone-800 px-6 py-2.5 text-sm font-medium text-white transition hover:bg-stone-700"
          >
            Score listings
          </button>
        )}
        <button
          onClick={onRetake}
          className="rounded-full border border-stone-300 px-6 py-2.5 text-sm font-medium text-stone-700 transition hover:bg-stone-100"
        >
          Retake the quiz
        </button>
      </div>
    </div>
  );
}
