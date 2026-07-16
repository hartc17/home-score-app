import { useMemo, useState } from "react";
import type { Rubric, RubricGates } from "@houseflavor/contracts";
import { Quiz } from "./quiz/Quiz.tsx";
import { Reveal } from "./quiz/Reveal.tsx";
import { GatesForm } from "./gates/GatesForm.tsx";
import { Compare } from "./compare/Compare.tsx";
import { mergeGates } from "./rubric/merge.ts";
import { inferProfile, type TasteProfile } from "./quiz/inference.ts";
import { clearRubric, loadRubric, saveRubric } from "./quiz/storage.ts";
import { optionsByIds, type QuizOption } from "./quiz/questions.ts";
import { saveRubricToServer } from "./api/client.ts";

type View = "reveal" | "gates" | "compare";

export default function App() {
  const stored = useMemo(() => loadRubric(), []);
  const [profile, setProfile] = useState<TasteProfile | null>(
    stored ? inferProfile(optionsByIds(stored.optionIds)) : null,
  );
  const [optionIds, setOptionIds] = useState<string[]>(stored?.optionIds ?? []);
  const [anonId, setAnonId] = useState<string | null>(stored?.anonId ?? null);
  const [view, setView] = useState<View>("reveal");

  function persist(rubric: Rubric, ids: string[]) {
    const record = saveRubric(rubric, ids, new Date().toISOString());
    if (record) {
      setAnonId(record.anonId);
      void saveRubricToServer(record.anonId, rubric);
    }
  }

  function handleComplete(picks: QuizOption[]) {
    const result = inferProfile(picks);
    const ids = picks.map((p) => p.id);
    setOptionIds(ids);
    persist(result.rubric, ids);
    setProfile(result);
  }

  function handleGatesSubmit(gates: RubricGates) {
    if (profile === null) return;
    const merged = mergeGates(profile.rubric, gates);
    persist(merged, optionIds);
    setProfile({ ...profile, rubric: merged });
    setView("reveal");
  }

  function handleRetake() {
    clearRubric();
    setProfile(null);
    setOptionIds([]);
    setView("reveal");
  }

  function render() {
    if (profile === null) return <Quiz onComplete={handleComplete} />;
    if (view === "gates") return <GatesForm onSubmit={handleGatesSubmit} onCancel={() => setView("reveal")} />;
    if (view === "compare" && anonId) {
      return <Compare anonId={anonId} rubric={profile.rubric} onBack={() => setView("reveal")} />;
    }
    return (
      <Reveal
        profile={profile}
        onRetake={handleRetake}
        onAddGates={() => setView("gates")}
        onScoreListings={anonId ? () => setView("compare") : undefined}
      />
    );
  }

  return <div className="min-h-screen bg-stone-50 text-stone-900">{render()}</div>;
}
