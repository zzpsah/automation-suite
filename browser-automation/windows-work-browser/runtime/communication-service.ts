export interface CommunicationMessage {
  destination: string;
  subject?: string;
  body: string;
  format?: "text" | "json";
}

export interface CommunicationProvider {
  send(message: CommunicationMessage): Promise<{ providerMessageId: string }>;
}

export class WebhookCommunicationProvider implements CommunicationProvider {
  private readonly endpoint: URL;
  private readonly fetchImpl: typeof fetch;

  constructor(endpoint: string, fetchImpl: typeof fetch = fetch) {
    const parsed = new URL(endpoint);
    if (!['https:'].includes(parsed.protocol)) throw new Error("Communication endpoints must use HTTPS.");
    this.endpoint = parsed;
    this.fetchImpl = fetchImpl;
  }

  async send(message: CommunicationMessage): Promise<{ providerMessageId: string }> {
    const response = await this.fetchImpl(this.endpoint, {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ destination: message.destination, subject: message.subject, body: message.body, format: message.format ?? "text" }),
    });
    if (!response.ok) throw new Error(`Communication provider returned HTTP ${response.status}.`);
    const requestId = response.headers.get("x-request-id") ?? `webhook-${Date.now()}`;
    return { providerMessageId: requestId };
  }
}

/** Explicit approval boundary for outbound side effects. */
export class ApprovedCommunicationService {
  constructor(private readonly provider: CommunicationProvider) {}

  async send(message: CommunicationMessage, approvalToken?: string): Promise<{ providerMessageId: string }> {
    if (!approvalToken) throw new Error("Explicit communication approval is required.");
    return this.provider.send(message);
  }
}
