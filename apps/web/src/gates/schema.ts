import type { RubricGates } from "@houseflavor/contracts";

export const HOME_TYPES = ["single_family", "townhouse", "condo"] as const;

export interface GatesForm {
  budget_max: string;
  districts: string;
  min_beds: string;
  min_baths: string;
  min_garage: string;
  home_types: string[];
  exclude_main_road: boolean;
  timeline: string;
}

export const EMPTY_GATES_FORM: GatesForm = {
  budget_max: "",
  districts: "",
  min_beds: "",
  min_baths: "",
  min_garage: "",
  home_types: ["single_family"],
  exclude_main_road: false,
  timeline: "",
};

export function validateGates(form: GatesForm): Record<string, string> {
  const errors: Record<string, string> = {};
  const budget = Number(form.budget_max);
  if (!form.budget_max || Number.isNaN(budget) || budget <= 0) {
    errors.budget_max = "Enter a budget above 0";
  }
  for (const key of ["min_beds", "min_baths", "min_garage"] as const) {
    const raw = form[key];
    if (raw === "") continue;
    const value = Number(raw);
    if (Number.isNaN(value) || value < 0) errors[key] = "Must be 0 or more";
  }
  if (form.home_types.length === 0) errors.home_types = "Pick at least one home type";
  return errors;
}

export function parseGates(form: GatesForm): RubricGates {
  return {
    budget_max: Number(form.budget_max),
    districts: form.districts
      .split(",")
      .map((d) => d.trim())
      .filter((d) => d.length > 0),
    min_beds: form.min_beds ? Number(form.min_beds) : 0,
    min_baths: form.min_baths ? Number(form.min_baths) : 0,
    min_garage: form.min_garage ? Number(form.min_garage) : 0,
    exclude_main_road: form.exclude_main_road,
    home_types: form.home_types,
    ...(form.timeline ? { timeline: form.timeline } : {}),
  };
}
