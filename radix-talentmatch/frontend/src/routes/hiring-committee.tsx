import { createFileRoute } from "@tanstack/react-router";
import { HiringCommittee } from "@/radix/pages/HiringCommittee";

export const Route = createFileRoute("/hiring-committee")({
  head: () => ({
    meta: [
      { title: "Hiring Committee · RADIX" },
      { name: "description", content: "Three interviewer personas deliberate on a candidate." },
      { property: "og:title", content: "Hiring Committee · RADIX" },
      { property: "og:description", content: "Three interviewer personas deliberate on a candidate." },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary_large_image" },
    ],
  }),
  component: HiringCommittee,
});
