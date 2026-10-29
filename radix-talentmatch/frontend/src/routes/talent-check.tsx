import { createFileRoute } from "@tanstack/react-router";
import { TalentCheck } from "@/radix/pages/Modules";

export const Route = createFileRoute("/talent-check")({
  head: () => ({
    meta: [
      { title: "Check readiness · RADIX" },
      { name: "description", content: "Compare a profile against a company hiring bar." },
      { property: "og:title", content: "Check readiness · RADIX" },
      { property: "og:description", content: "Compare a profile against a company hiring bar." },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary_large_image" },
    ],
  }),
  component: TalentCheck,
});
