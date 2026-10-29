import { createFileRoute } from "@tanstack/react-router";
import { CompanyIntel } from "@/radix/pages/CompanyIntel";

export const Route = createFileRoute("/company-intel")({
  head: () => ({
    meta: [
      { title: "Company Intel · RADIX" },
      { name: "description", content: "Consensus dossiers on company hiring rounds and skill bars." },
      { property: "og:title", content: "Company Intel · RADIX" },
      { property: "og:description", content: "Consensus dossiers on company hiring rounds and skill bars." },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary_large_image" },
    ],
  }),
  component: CompanyIntel,
});
