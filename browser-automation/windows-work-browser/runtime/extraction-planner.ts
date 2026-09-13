import type { ExtractionJob, ExtractionFormat } from "../agent/extraction-contract";

export interface PlannedExtractionStep {
  operation: "open" | "list" | "extract" | "next" | "detail" | "deduplicate" | "export";
  description: string;
}

export interface PlannerInput {
  sourceDescription: string;
  detailTraversal?: boolean;
  deduplicateBy?: string[];
}

export function buildExtractionSteps(job: ExtractionJob, input: PlannerInput): PlannedExtractionStep[] {
  const steps: PlannedExtractionStep[] = [
    { operation: "open", description: `Open source: ${input.sourceDescription} (${job.source.startUrl})` },
    { operation: "list", description: job.source.listSelector ? `Identify records using ${job.source.listSelector}.` : "Identify record/listing elements." },
    { operation: "extract", description: `Extract fields: ${job.fields.join(", ")}` },
  ];

  if (input.detailTraversal || job.source.detailSelector) {
    steps.push({ operation: "detail", description: "Open each detail record and extract declared fields." });
  }
  if (job.source.pagination) {
    steps.push({ operation: "next", description: `Traverse pagination using ${job.source.pagination.strategy}.` });
  }
  if (input.deduplicateBy?.length) {
    steps.push({ operation: "deduplicate", description: `Deduplicate by: ${input.deduplicateBy.join(", ")}` });
  }
  const format: ExtractionFormat = job.format;
  steps.push({ operation: "export", description: `Export as ${format}.` });
  return steps;
}
