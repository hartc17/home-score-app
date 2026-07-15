import { useMemo, useState } from "react";
import { Quiz } from "./quiz/Quiz.tsx";
import { Reveal } from "./quiz/Reveal.tsx";
import { inferProfile, type TasteProfile } from "./quiz/inference.ts";
import { clearRubric, loadRubric, saveRubric } from "./quiz/storage.ts";
import { optionsByIds, type QuizOption } from "./quiz/questions.ts";

export default function App() {
  const stored = useMemo(() => loadRubric(), []);
  const [profile, setProfile] = useState<TasteProfile | null>(
    stored ? inferProfile(optionsByIds(stored.optionIds)) : null,
  );

  function handleComplete(picks: QuizOption[]) {
    const result = inferProfile(picks);
    saveRubric(result.rubric, picks.map((p) => p.id), new Date().toISOString());
    setProfile(result);
  }

  function handleRetake() {
    clearRubric();
    setProfile(null);
  }

  return (
    <div className="min-h-screen bg-stone-50 text-stone-900">
      {profile ? <Reveal profile={profile} onRetake={handleRetake} /> : <Quiz onComplete={handleComplete} />}
    </div>
  );
}
