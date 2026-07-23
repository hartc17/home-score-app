import { useState, type FormEvent } from "react";
import { AuthError, requestMagicLink } from "../api/client.ts";

type Status = "idle" | "sending" | "sent" | "error";

export function Account({
  anonId,
  email,
  onSignOut,
}: {
  anonId: string | null;
  email: string | null;
  onSignOut: () => void;
}) {
  const [open, setOpen] = useState(false);
  const [value, setValue] = useState("");
  const [status, setStatus] = useState<Status>("idle");
  const [error, setError] = useState<string | null>(null);

  if (email) {
    return (
      <div className="flex items-center gap-3 text-sm text-stone-500">
        <span>
          Signed in as <span className="font-medium text-stone-700">{email}</span>
        </span>
        <button onClick={onSignOut} className="underline hover:text-stone-700">
          Sign out
        </button>
      </div>
    );
  }

  if (status === "sent") {
    return (
      <p role="status" className="text-sm text-stone-500">
        Check your email for a sign-in link.
      </p>
    );
  }

  if (!open) {
    return (
      <button onClick={() => setOpen(true)} className="text-sm font-medium text-stone-600 underline hover:text-stone-800">
        Save your profile
      </button>
    );
  }

  async function submit(event: FormEvent) {
    event.preventDefault();
    setStatus("sending");
    setError(null);
    try {
      await requestMagicLink(value.trim(), anonId);
      setStatus("sent");
    } catch (err) {
      setStatus("error");
      setError(err instanceof AuthError ? err.message : "Something went wrong");
    }
  }

  return (
    <form onSubmit={(e) => void submit(e)} className="flex items-center gap-2">
      <input
        type="email"
        value={value}
        placeholder="you@email.com"
        onChange={(e) => setValue(e.target.value)}
        aria-label="Email address"
        className="rounded-lg border border-stone-300 px-3 py-1.5 text-sm focus:border-stone-500 focus:outline-none"
      />
      <button
        type="submit"
        disabled={status === "sending"}
        className="rounded-lg bg-stone-800 px-4 py-1.5 text-sm font-medium text-white transition hover:bg-stone-700 disabled:opacity-50"
      >
        {status === "sending" ? "Sending..." : "Send link"}
      </button>
      {error && (
        <span role="alert" className="text-sm text-red-600">
          {error}
        </span>
      )}
    </form>
  );
}
