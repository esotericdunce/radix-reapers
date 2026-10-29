import { createFileRoute } from "@tanstack/react-router";
import { JDAnalytics } from "@/radix/pages/Modules";

export const Route = createFileRoute("/jd-analytics")({
  head: () => ({
    meta: [
      { title: "Read the role · RADIX" },
      { name: "description", content: "Extract required skills and evidence from any job description." },
      { property: "og:title", content: "Read the role · RADIX" },
      { property: "og:description", content: "Extract required skills and evidence from any job description." },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary_large_image" },
    ],
  }),
  component: JDAnalytics,
});
