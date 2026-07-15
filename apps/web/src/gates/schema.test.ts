import { describe, expect, it } from "vitest";
import { EMPTY_GATES_FORM, parseGates, validateGates, type GatesForm } from "./schema.ts";

function form(overrides: Partial<GatesForm> = {}): GatesForm {
  return { ...EMPTY_GATES_FORM, budget_max: "600000", min_beds: "3", min_baths: "2", ...overrides };
}

describe("validateGates", () => {
  it("test_validate_valid_form_has_no_errors", () => {
    expect(validateGates(form())).toEqual({});
  });

  it("test_validate_missing_budget_is_error", () => {
    expect(validateGates(form({ budget_max: "" })).budget_max).toBeTruthy();
  });

  it("test_validate_negative_beds_is_error", () => {
    expect(validateGates(form({ min_beds: "-1" })).min_beds).toBeTruthy();
  });

  it("test_validate_no_home_types_is_error", () => {
    expect(validateGates(form({ home_types: [] })).home_types).toBeTruthy();
  });
});

describe("parseGates", () => {
  it("test_parse_splits_districts_and_coerces_numbers", () => {
    const gates = parseGates(form({ districts: "Saratoga Springs, Ballston Spa ,", min_garage: "2" }));
    expect(gates.budget_max).toBe(600000);
    expect(gates.districts).toEqual(["Saratoga Springs", "Ballston Spa"]);
    expect(gates.min_beds).toBe(3);
    expect(gates.min_garage).toBe(2);
  });

  it("test_parse_defaults_blank_minimums_to_zero", () => {
    const gates = parseGates(form({ min_garage: "" }));
    expect(gates.min_garage).toBe(0);
  });

  it("test_parse_omits_timeline_when_blank", () => {
    expect(parseGates(form()).timeline).toBeUndefined();
  });
});
