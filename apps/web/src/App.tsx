import { useMemo, useState } from "react";
import type { RubricGates } from "@houseflavor/contracts";
import { Quiz } from "./quiz/Quiz.tsx";
import { Reveal } from "./quiz/Reveal.tsx";
import { GatesForm } from "./gates/GatesForm.tsx";
import { mergeGates } from "./rubric/merge.ts";
import { inferProfile, type TasteProfile } from "./quiz/inference.ts";
import { clearRubric, loadRubric, saveRubric } from "./quiz/storage.ts";
import { optionsByIds, type QuizOption } from "./quiz/questions.ts";

export default function App() {
  const stored = useMemo(() => loadRubric(), []);
  const [profile, setProfile] = useState<TasteProfile | null>(
    stored ? inferProfile(optionsByIds(stored.optionIds)) : null,
  );
  const [optionIds, setOptionIds] = useState<string[]>(stored?.optionIds ?? []);
  const [showGates, setShowGates] = useState(false);

  function handleComplete(picks: QuizOption[]) {
    const result = inferProfile(picks);
    const ids = picks.map((p) => p.id);
    setOptionIds(ids);
    saveRubric(result.rubric, ids, new Date().toISOString());
    setProfile(result);
  }

  function handleGatesSubmit(gates: RubricGates) {
    if (profile === null) return;
    const merged = mergeGates(profile.rubric, gates);
    saveRubric(merged, optionIds, new Date().toISOString());
    setProfile({ ...profile, rubric: merged });
    setShowGates(false);
  }

  function handleRetake() {
    clearRubric();
    setProfile(null);
    setOptionIds([]);
    setShowGates(false);
  }

  return (
    <div className="min-h-screen bg-stone-50 text-stone-900">
      {profile === null ? (
        <Quiz onComplete={handleComplete} />
      ) : showGates ? (
        <GatesForm onSubmit={handleGatesSubmit} onCancel={() => setShowGates(false)} />
      ) : (
        <Reveal profile={profile} onRetake={handleRetake} onAddGates={() => setShowGates(true)} />
      )}
    </div>
  );
}
