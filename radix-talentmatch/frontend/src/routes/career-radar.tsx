import { createFileRoute } from "@tanstack/react-router";
import { CareerRadar } from "@/radix/pages/CareerRadar";

export const Route = createFileRoute("/career-radar")({
  head: () => ({
    meta: [
      { title: "Career Radar · RADIX" },
      { name: "description", content: "Placement tier readiness and the highest-ROI skill leaps." },
      { property: "og:title", content: "Career Radar · RADIX" },
      { property: "og:description", content: "Placement tier readiness and the highest-ROI skill leaps." },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary_large_image" },
    ],
  }),
  component: CareerRadar,
});
