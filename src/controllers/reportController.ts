import { FingerprintInput, FingerprintReport } from "../models/types";
import { GroqClient } from "../infra/groqClient";
import { AIService } from "../services/ai/AIService";

export async function generateReport(input: FingerprintInput): Promise<FingerprintReport> {
  const client = new GroqClient();
  const svc = new AIService(client);
  return svc.generateReport(input);
}
