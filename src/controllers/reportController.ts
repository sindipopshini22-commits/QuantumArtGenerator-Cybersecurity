import { FingerprintInput, FingerprintReport } from "../models/types";
import { OpenAIClient } from "../infra/openaiClient";
import { AIService } from "../services/ai/AIService";

export async function generateReport(input: FingerprintInput): Promise<FingerprintReport> {
  const client = new OpenAIClient();
  const svc = new AIService(client);
  return svc.generateReport(input);
}
