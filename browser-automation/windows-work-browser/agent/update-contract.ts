export type PromotionState =
  | "discovered"
  | "staged"
  | "verified"
  | "installed"
  | "smoke-passed"
  | "overlay-passed"
  | "candidate"
  | "released"
  | "rolled-back";

export interface ReleaseArtifactRef {
  version: string;
  platform: "windows";
  arch: "x64" | "arm64";
  filename: string;
  sha256: string;
  sourceUrl: string;
}

export interface ReleaseState {
  current?: ReleaseArtifactRef;
  previousVerified?: ReleaseArtifactRef;
  state: PromotionState;
  evidenceRefs: string[];
  updatedAt: string;
}

export interface UpdateManager {
  stage(candidate: ReleaseArtifactRef): Promise<void>;
  verify(candidate: ReleaseArtifactRef): Promise<void>;
  promote(candidate: ReleaseArtifactRef): Promise<void>;
  rollback(): Promise<void>;
  state(): Promise<ReleaseState>;
}

/** Promotion must only happen after immutable artifact verification. */
export function assertPromotionReady(state: ReleaseState): void {
  if (state.state !== "candidate") {
    throw new Error(`Release is not promotable from state: ${state.state}`);
  }
  if (!state.current?.sha256 || state.current.sha256.length !== 64) {
    throw new Error("Candidate is missing a verified SHA-256 digest.");
  }
  if (state.evidenceRefs.length === 0) {
    throw new Error("Candidate has no retained evidence references.");
  }
}
