import { createFileRoute } from "@tanstack/react-router";
import { SkillMatching } from "@/radix/pages/Modules";

export const Route = createFileRoute("/skill-matching")({
  head: () => ({
    meta: [
      { title: "Measure the fit · RADIX" },
      { name: "description", content: "Score a candidate against a specific job description." },
      { property: "og:title", content: "Measure the fit · RADIX" },
      { property: "og:description", content: "Score a candidate against a specific job description." },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary_large_image" },
    ],
  }),
  component: SkillMatching,
});
