import { useEffect, useState } from "react";
import type { Rubric, ScoredListing } from "@houseflavor/contracts";
import { listScores, runScore, saveRubricToServer, ScoreError } from "../api/client.ts";

const VERDICT_STYLE: Record<string, string> = {
  pursue: "bg-green-100 text-green-800",
  showing: "bg-amber-100 text-amber-800",
  conditional: "bg-stone-200 text-stone-700",
  weak: "bg-red-100 text-red-700",
};

function priceLabel(price?: number): string {
  return price ? `$${price.toLocaleString()}` : "-";
}

export function Compare({ anonId, rubric, onBack }: { anonId: string; rubric: Rubric; onBack: () => void }) {
  const [url, setUrl] = useState("");
  const [listings, setListings] = useState<ScoredListing[]>([]);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function refresh() {
    setListings(await listScores(anonId));
  }

  useEffect(() => {
    // Make sure the rubric exists server-side before scoring against it. Mount-only.
    saveRubricToServer(anonId, rubric).then(refresh);
  }, []);

  async function handleScore() {
    if (!url.trim()) return;
    setBusy(true);
    setError(null);
    try {
      await runScore(anonId, url.trim());
      setUrl("");
      await refresh();
    } catch (e) {
      setError(e instanceof ScoreError ? e.message : "Something went wrong");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="mx-auto max-w-3xl px-6 py-12">
      <div className="mb-6 flex items-center justify-between">
        <h1 className="text-3xl font-bold text-stone-800">Score listings</h1>
        <button onClick={onBack} className="text-sm text-stone-500 hover:text-stone-700">
          Back to profile
        </button>
      </div>
      <p className="mb-6 text-stone-500">
        Paste a listing URL. It is scored against your taste and ranked below.
      </p>

      <div className="flex gap-2">
        <input
          type="url"
          value={url}
          placeholder="https://..."
          onChange={(e) => setUrl(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && handleScore()}
          className="flex-1 rounded-lg border border-stone-300 px-3 py-2 focus:border-stone-500 focus:outline-none"
        />
        <button
          onClick={handleScore}
          disabled={busy}
          className="rounded-lg bg-stone-800 px-5 py-2 text-sm font-medium text-white transition hover:bg-stone-700 disabled:opacity-50"
        >
          {busy ? "Scoring..." : "Score"}
        </button>
      </div>
      {error && <p className="mt-2 text-sm text-red-600">{error}</p>}

      {listings.length === 0 ? (
        <p className="mt-10 text-center text-stone-400">No scored listings yet.</p>
      ) : (
        <ul className="mt-8 space-y-3">
          {listings.map((listing, i) => (
            <li
              key={listing.listing_id}
              className="flex items-center gap-4 rounded-xl border border-stone-200 bg-white px-4 py-3"
            >
              <span className="w-6 text-center text-lg font-semibold text-stone-400">{i + 1}</span>
              <div className="min-w-0 flex-1">
                <p className="truncate font-medium text-stone-800">{listing.address ?? listing.url}</p>
                <p className="text-sm text-stone-500">{priceLabel(listing.price)}</p>
              </div>
              <span
                className={`rounded-full px-2.5 py-0.5 text-xs font-medium capitalize ${
                  VERDICT_STYLE[listing.verdict] ?? VERDICT_STYLE.weak
                }`}
              >
                {listing.verdict}
              </span>
              <span className="w-12 text-right text-2xl font-bold text-stone-800">{Math.round(listing.total)}</span>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
