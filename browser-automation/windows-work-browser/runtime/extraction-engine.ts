export interface ExtractedRecord {
  [field: string]: string | number | boolean | null;
}

export interface ExtractionRun {
  records: ExtractedRecord[];
  expectedCount?: number;
  deduplicateBy?: string[];
}

export interface ExtractionResult {
  records: ExtractedRecord[];
  duplicatesRemoved: number;
  missingFieldCount: number;
  countVerified: boolean;
  exported: string;
}

export function deduplicateRecords(records: ExtractedRecord[], keys: string[]): { records: ExtractedRecord[]; removed: number } {
  if (keys.length === 0) return { records: [...records], removed: 0 };
  const seen = new Set<string>();
  const unique: ExtractedRecord[] = [];
  for (const record of records) {
    const key = JSON.stringify(keys.map((field) => record[field] ?? null));
    if (seen.has(key)) continue;
    seen.add(key);
    unique.push(record);
  }
  return { records: unique, removed: records.length - unique.length };
}

export function verifyRequiredFields(records: ExtractedRecord[], fields: string[]): number {
  let missing = 0;
  for (const record of records) {
    for (const field of fields) {
      const value = record[field];
      if (value === undefined || value === null || value === "") missing += 1;
    }
  }
  return missing;
}

export function exportRecords(records: ExtractedRecord[], format: "json" | "csv"): string {
  if (format === "json") return JSON.stringify(records, null, 2);
  const fields = [...new Set(records.flatMap((record) => Object.keys(record)))];
  const quote = (value: unknown): string => {
    const text = value == null ? "" : String(value);
    return `"${text.replaceAll('"', '""')}"`;
  };
  return [
    fields.map(quote).join(","),
    ...records.map((record) => fields.map((field) => quote(record[field])).join(",")),
  ].join("\n");
}

export function runExtraction(run: ExtractionRun, requiredFields: string[], format: "json" | "csv"): ExtractionResult {
  const deduped = deduplicateRecords(run.records, run.deduplicateBy ?? []);
  const missingFieldCount = verifyRequiredFields(deduped.records, requiredFields);
  const countVerified = run.expectedCount === undefined || run.expectedCount === deduped.records.length;
  return {
    records: deduped.records,
    duplicatesRemoved: deduped.removed,
    missingFieldCount,
    countVerified,
    exported: exportRecords(deduped.records, format),
  };
}
