import { createFileRoute } from "@tanstack/react-router";
import { ResumeParser } from "@/radix/pages/Modules";

export const Route = createFileRoute("/resume-parser")({
  head: () => ({
    meta: [
      { title: "Read the resume · RADIX" },
      { name: "description", content: "Extract candidate skills and experience from a resume." },
      { property: "og:title", content: "Read the resume · RADIX" },
      { property: "og:description", content: "Extract candidate skills and experience from a resume." },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary_large_image" },
    ],
  }),
  component: ResumeParser,
});
