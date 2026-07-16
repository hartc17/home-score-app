import { useEffect, useMemo, useRef, useState } from "react";
import type { Rubric, RubricGates } from "@houseflavor/contracts";
import { Quiz } from "./quiz/Quiz.tsx";
import { Reveal } from "./quiz/Reveal.tsx";
import { GatesForm } from "./gates/GatesForm.tsx";
import { Compare } from "./compare/Compare.tsx";
import { Account } from "./account/Account.tsx";
import { mergeGates } from "./rubric/merge.ts";
import { inferProfile, type TasteProfile } from "./quiz/inference.ts";
import {
  clearRubric,
  clearSession,
  loadRubric,
  loadSession,
  saveRubric,
  saveSession,
  type StoredSession,
} from "./quiz/storage.ts";
import { optionsByIds, type QuizOption } from "./quiz/questions.ts";
import { saveRubricToServer, verifyMagicLink } from "./api/client.ts";

type View = "reveal" | "gates" | "compare";

export default function App() {
  const stored = useMemo(() => loadRubric(), []);
  const [profile, setProfile] = useState<TasteProfile | null>(
    stored ? inferProfile(optionsByIds(stored.optionIds)) : null,
  );
  const [optionIds, setOptionIds] = useState<string[]>(stored?.optionIds ?? []);
  const [anonId, setAnonId] = useState<string | null>(stored?.anonId ?? null);
  const [session, setSession] = useState<StoredSession | null>(() => loadSession());
  const [view, setView] = useState<View>("reveal");

  // A magic-link landing arrives as ?token=...; verify it, store the session,
  // then strip the token from the URL so a reload cannot replay it. The ref
  // guard keeps a one-time token from being spent twice under StrictMode.
  const claimed = useRef(false);
  useEffect(() => {
    const token = new URLSearchParams(window.location.search).get("token");
    if (!token || claimed.current) return;
    claimed.current = true;
    verifyMagicLink(token)
      .then((s) => {
        const next = { session: s.session, email: s.email };
        saveSession(next);
        setSession(next);
      })
      .catch(() => undefined)
      .finally(() => window.history.replaceState({}, "", window.location.pathname));
  }, []);

  function signOut() {
    clearSession();
    setSession(null);
  }

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

  return (
    <div className="min-h-screen bg-stone-50 text-stone-900">
      {profile !== null && (
        <div className="mx-auto flex max-w-4xl justify-end px-6 pt-4">
          <Account anonId={anonId} email={session?.email ?? null} onSignOut={signOut} />
        </div>
      )}
      {render()}
    </div>
  );
}
