import { createFileRoute } from "@tanstack/react-router";
import { ProfileBuilder } from "@/radix/pages/Modules";

export const Route = createFileRoute("/profile")({
  head: () => ({
    meta: [
      { title: "Shape the profile · RADIX" },
      { name: "description", content: "Rate skills and attach evidence for matching and readiness." },
      { property: "og:title", content: "Shape the profile · RADIX" },
      { property: "og:description", content: "Rate skills and attach evidence for matching and readiness." },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary_large_image" },
    ],
  }),
  component: ProfileBuilder,
});
