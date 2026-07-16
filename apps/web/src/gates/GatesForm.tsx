import { useState, type FormEvent } from "react";
import type { RubricGates } from "@houseflavor/contracts";
import { EMPTY_GATES_FORM, HOME_TYPES, parseGates, validateGates, type GatesForm as GatesFormState } from "./schema.ts";

const HOME_TYPE_LABEL: Record<string, string> = {
  single_family: "Single family",
  townhouse: "Townhouse",
  condo: "Condo",
};

const NUMBER_FIELDS: { key: "budget_max" | "min_beds" | "min_baths" | "min_garage"; label: string; placeholder: string }[] = [
  { key: "budget_max", label: "Budget ceiling", placeholder: "600000" },
  { key: "min_beds", label: "Min beds", placeholder: "3" },
  { key: "min_baths", label: "Min baths", placeholder: "2" },
  { key: "min_garage", label: "Min garage", placeholder: "2" },
];

export function GatesForm({
  onSubmit,
  onCancel,
}: {
  onSubmit: (gates: RubricGates) => void;
  onCancel: () => void;
}) {
  const [form, setForm] = useState<GatesFormState>(EMPTY_GATES_FORM);
  const [errors, setErrors] = useState<Record<string, string>>({});

  function set<K extends keyof GatesFormState>(key: K, value: GatesFormState[K]) {
    setForm((f) => ({ ...f, [key]: value }));
  }

  function toggleHomeType(type: string) {
    setForm((f) => ({
      ...f,
      home_types: f.home_types.includes(type)
        ? f.home_types.filter((t) => t !== type)
        : [...f.home_types, type],
    }));
  }

  function submit(event: FormEvent) {
    event.preventDefault();
    const found = validateGates(form);
    setErrors(found);
    if (Object.keys(found).length === 0) onSubmit(parseGates(form));
  }

  return (
    <form onSubmit={submit} className="mx-auto max-w-2xl px-6 py-12">
      <h1 className="mb-1 text-3xl font-bold text-stone-800">Your must-haves</h1>
      <p className="mb-8 text-stone-500">
        These are the hard limits we will never score around. Everything else is your taste.
      </p>

      <div className="grid grid-cols-2 gap-4">
        {NUMBER_FIELDS.map((field) => (
          <label key={field.key} className="block">
            <span className="mb-1 block text-sm font-medium text-stone-600">{field.label}</span>
            <input
              type="number"
              inputMode="numeric"
              value={form[field.key]}
              placeholder={field.placeholder}
              onChange={(e) => set(field.key, e.target.value)}
              aria-invalid={errors[field.key] ? true : undefined}
              aria-describedby={errors[field.key] ? `${field.key}-error` : undefined}
              className="w-full rounded-lg border border-stone-300 px-3 py-2 focus:border-stone-500 focus:outline-none"
            />
            {errors[field.key] && (
              <span id={`${field.key}-error`} className="mt-1 block text-xs text-red-600">
                {errors[field.key]}
              </span>
            )}
          </label>
        ))}
      </div>

      <label className="mt-4 block">
        <span className="mb-1 block text-sm font-medium text-stone-600">Target districts</span>
        <input
          type="text"
          value={form.districts}
          placeholder="Saratoga Springs, Ballston Spa"
          onChange={(e) => set("districts", e.target.value)}
          className="w-full rounded-lg border border-stone-300 px-3 py-2 focus:border-stone-500 focus:outline-none"
        />
        <span className="mt-1 block text-xs text-stone-400">Comma separated. Leave blank for any.</span>
      </label>

      <div className="mt-4">
        <span className="mb-2 block text-sm font-medium text-stone-600">Home types</span>
        <div className="flex flex-wrap gap-2">
          {HOME_TYPES.map((type) => {
            const active = form.home_types.includes(type);
            return (
              <button
                key={type}
                type="button"
                onClick={() => toggleHomeType(type)}
                className={`rounded-full border px-4 py-1.5 text-sm transition ${
                  active
                    ? "border-stone-800 bg-stone-800 text-white"
                    : "border-stone-300 text-stone-600 hover:bg-stone-100"
                }`}
              >
                {HOME_TYPE_LABEL[type]}
              </button>
            );
          })}
        </div>
        {errors.home_types && (
          <span id="home_types-error" className="mt-1 block text-xs text-red-600">
            {errors.home_types}
          </span>
        )}
      </div>

      <label className="mt-5 flex items-center gap-2">
        <input
          type="checkbox"
          checked={form.exclude_main_road}
          onChange={(e) => set("exclude_main_road", e.target.checked)}
          className="h-4 w-4 rounded border-stone-300"
        />
        <span className="text-sm text-stone-700">Exclude homes on a main road</span>
      </label>

      <div className="mt-10 flex items-center gap-3">
        <button
          type="submit"
          className="rounded-full bg-stone-800 px-6 py-2.5 text-sm font-medium text-white transition hover:bg-stone-700"
        >
          Save must-haves
        </button>
        <button type="button" onClick={onCancel} className="text-sm text-stone-500 hover:text-stone-700">
          Back
        </button>
      </div>
    </form>
  );
}
