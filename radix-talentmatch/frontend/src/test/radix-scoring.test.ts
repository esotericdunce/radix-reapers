import { beforeEach, describe, expect, it } from "vitest";
import { demoApi } from "@/radix/services/demo";

describe("RADIX demo scoring", () => {
  beforeEach(() => localStorage.clear());

  it("readiness averages capped candidate/required ratios (Ananya vs Google = 58%)", async () => {
    const r = await demoApi.talent("ananya-rao", "Google");
    expect(r.readiness_score).toBe(58);
  });

  it("match score is matched requirements over detected requirements", async () => {
    const r = await demoApi.match("ananya-rao", "google-swe");
    const total = r.matched_skills.length + r.missing_skills.length;
    expect(r.match_score).toBe(Math.round((100 * r.matched_skills.length) / total));
  });
});
