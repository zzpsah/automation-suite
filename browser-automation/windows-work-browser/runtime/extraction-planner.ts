import type { ExtractionField, ExtractionPlan } from "../agent/extractor-contract";

export interface PlannedExtractionStep {
  operation: "open" | "list" | "extract" | "next" | "detail" | "deduplicate" | "export";
  description: string;
}

export function buildExtractionSteps(plan: ExtractionPlan): PlannedExtractionStep[] {
  const steps: PlannedExtractionStep[] = [
    { operation: "open", description: `Open source: ${plan.sourceDescription}` },
    { operation: "list", description: "Identify record/listing elements." },
    { operation: "extract", description: `Extract fields: ${plan.fields.map((f: ExtractionField) => f.name).join(", ")}` },
  ];
  if (plan.detailTraversal?.length) {
    steps.push({ operation: "detail", description: "Open each detail record and extract declared fields." });
  }
  if (plan.pagination) {
    steps.push({ operation: "next", description: `Traverse pagination using: ${plan.pagination.nextAction}` });
  }
  if (plan.deduplicateBy?.length) {
    steps.push({ operation: "deduplicate", description: `Deduplicate by: ${plan.deduplicateBy.join(", ")}` });
  }
  steps.push({ operation: "export", description: `Export as ${plan.output}.` });
  return steps;
}
