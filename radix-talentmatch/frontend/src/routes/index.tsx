import { createFileRoute } from "@tanstack/react-router";
import { Overview } from "@/radix/pages/Modules";

export const Route = createFileRoute("/")({
  head: () => ({
    meta: [
      { title: "RADIX — Know where you stand" },
      { name: "description", content: "See your skill profile, role match and readiness at a glance." },
      { property: "og:title", content: "RADIX — Know where you stand" },
      { property: "og:description", content: "See your skill profile, role match and readiness at a glance." },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary_large_image" },
    ],
  }),
  component: Overview,
});
