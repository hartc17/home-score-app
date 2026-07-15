import { useMemo, useState } from "react";
import type { RubricGates } from "@houseflavor/contracts";
import { Quiz } from "./quiz/Quiz.tsx";
import { Reveal } from "./quiz/Reveal.tsx";
import { GatesForm } from "./gates/GatesForm.tsx";
import { mergeGates } from "./rubric/merge.ts";
import { inferProfile, type TasteProfile } from "./quiz/inference.ts";
import { clearRubric, loadRubric, saveRubric } from "./quiz/storage.ts";
import { optionsByIds, type QuizOption } from "./quiz/questions.ts";
import { saveRubricToServer } from "./api/client.ts";
import type { Rubric } from "@houseflavor/contracts";

export default function App() {
  const stored = useMemo(() => loadRubric(), []);
  const [profile, setProfile] = useState<TasteProfile | null>(
    stored ? inferProfile(optionsByIds(stored.optionIds)) : null,
  );
  const [optionIds, setOptionIds] = useState<string[]>(stored?.optionIds ?? []);
  const [showGates, setShowGates] = useState(false);

  function persist(rubric: Rubric, ids: string[]) {
    const record = saveRubric(rubric, ids, new Date().toISOString());
    if (record) void saveRubricToServer(record.anonId, rubric);
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
