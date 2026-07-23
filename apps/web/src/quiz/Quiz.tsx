import { useCallback, useEffect, useState } from "react";
import { QUESTIONS, type QuizOption } from "./questions.ts";
import { OptionImage } from "./OptionImage.tsx";

export function Quiz({ onComplete }: { onComplete: (picks: QuizOption[]) => void }) {
  const [picks, setPicks] = useState<QuizOption[]>([]);
  const index = picks.length;

  // Functional update keeps rapid key/click events from reading a stale `picks`
  // and recording a duplicate answer.
  const choose = useCallback((side: 0 | 1) => {
    setPicks((prev) => (prev.length >= QUESTIONS.length ? prev : [...prev, QUESTIONS[prev.length].options[side]]));
  }, []);

  useEffect(() => {
    if (picks.length === QUESTIONS.length) onComplete(picks);
  }, [picks, onComplete]);

  useEffect(() => {
    function onKey(e: KeyboardEvent) {
      if (e.key === "ArrowLeft" || e.key === "1") choose(0);
      else if (e.key === "ArrowRight" || e.key === "2") choose(1);
    }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [choose]);

  if (index >= QUESTIONS.length) return null;
  const question = QUESTIONS[index];
  const progress = (index / QUESTIONS.length) * 100;

  return (
    <div className="mx-auto flex min-h-screen max-w-4xl flex-col px-6 py-10">
      <div className="mb-8">
        <div className="mb-2 flex items-center justify-between text-sm text-stone-500">
          <span className="font-medium tracking-wide">HouseFlavor</span>
          <span>
            {index + 1} / {QUESTIONS.length}
          </span>
        </div>
        <div
          className="h-1.5 w-full overflow-hidden rounded-full bg-stone-200"
          role="progressbar"
          aria-label={`Question ${index + 1} of ${QUESTIONS.length}`}
          aria-valuenow={index}
          aria-valuemin={0}
          aria-valuemax={QUESTIONS.length}
        >
          <div className="h-full rounded-full bg-stone-800 transition-all duration-300" style={{ width: `${progress}%` }} />
        </div>
      </div>

      <h2 className="mb-8 text-center text-2xl font-semibold text-stone-800">{question.prompt}</h2>

      <div className="flex flex-1 items-center">
        <div className="grid w-full grid-cols-1 gap-5 sm:grid-cols-2">
          {question.options.map((option, side) => (
            <button
              key={option.id}
              onClick={() => choose(side as 0 | 1)}
              className="group relative aspect-[4/3] overflow-hidden rounded-2xl border border-stone-200 bg-white shadow-sm ring-stone-800 transition hover:-translate-y-1 hover:shadow-md focus:outline-none focus-visible:ring-2"
              aria-label={`Option ${side + 1}`}
            >
              <OptionImage option={option} />
              <span className="absolute left-3 top-3 flex h-7 w-7 items-center justify-center rounded-full bg-white/85 text-sm font-semibold text-stone-700 shadow">
                {side + 1}
              </span>
            </button>
          ))}
        </div>
      </div>

      <p className="mt-8 text-center text-sm text-stone-400">
        Tap a photo, or use the arrow keys. No wrong answers.
      </p>
    </div>
  );
}
