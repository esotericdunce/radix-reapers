import { createFileRoute } from "@tanstack/react-router";
import { InterviewArena } from "@/radix/pages/InterviewArena";

export const Route = createFileRoute("/interview-arena")({
  head: () => ({
    meta: [
      { title: "Mock Interview · RADIX" },
      { name: "description", content: "Calibrated scenario interviews graded by Bloom depth." },
      { property: "og:title", content: "Mock Interview · RADIX" },
      { property: "og:description", content: "Calibrated scenario interviews graded by Bloom depth." },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary_large_image" },
    ],
  }),
  component: InterviewArena,
});
