export type ExtractionScope =
  | "current-page"
  | "all-pages"
  | "selected-records"
  | "all-records";

export type ExtractionFormat = "csv" | "xlsx" | "json" | "pdf";

export interface ExtractionField {
  name: string;
  selector?: string;
  semanticHint?: string;
  required: boolean;
}

export interface ExtractionPlan {
  id: string;
  sourceDescription: string;
  scope: ExtractionScope;
  fields: ExtractionField[];
  pagination?: { nextAction: string; maxPages?: number };
  detailTraversal?: string[];
  output: ExtractionFormat;
  deduplicateBy?: string[];
  resumable: boolean;
}

export interface ExtractionCheckpoint {
  planId: string;
  pageIndex: number;
  recordCount: number;
  completedRecordKeys: string[];
  outputReference?: string;
  updatedAt: string;
}

export interface ExtractionPreview {
  estimatedRecords?: number;
  fields: string[];
  duplicateCount: number;
  missingRequiredCount: number;
}

export interface ExtractionResult {
  ok: boolean;
  planId: string;
  recordCount: number;
  outputReference?: string;
  sourceVerification: {
    observedRecords?: number;
    verified: boolean;
    summary: string;
  };
  error?: { code: string; message: string; recoverable: boolean };
}

export interface UniversalExtractor {
  preview(plan: ExtractionPlan): Promise<ExtractionPreview>;
  run(plan: ExtractionPlan, checkpoint?: ExtractionCheckpoint): Promise<ExtractionResult>;
}
