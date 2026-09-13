export type ExtractionFormat = "csv" | "xlsx" | "json" | "pdf";
export type ExtractionStatus = "queued" | "running" | "paused" | "failed" | "completed" | "cancelled";

export interface ExtractionSource {
  startUrl: string;
  listSelector?: string;
  detailSelector?: string;
  pagination?: { strategy: "next" | "pages" | "infinite-scroll"; limit?: number };
}

export interface ExtractionJob {
  id: string;
  workspaceId: string;
  source: ExtractionSource;
  fields: string[];
  format: ExtractionFormat;
  status: ExtractionStatus;
  processed: number;
  total?: number;
  checkpoint?: string;
  outputReference?: string;
  createdAt: string;
  updatedAt: string;
}

export interface ExtractionPreview {
  estimatedRecords?: number;
  fields: string[];
  duplicateCount?: number;
  missingFieldCount?: number;
}
