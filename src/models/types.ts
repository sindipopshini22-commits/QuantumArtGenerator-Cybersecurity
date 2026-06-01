export type RandomnessMetrics = Record<string, number>;

export interface ArtworkMetadata {
  title?: string;
  artist?: string;
  creationDate?: string;
  attributes?: Record<string, string>;
}

export interface FingerprintInput {
  cryptographicKey: string;
  entropyScore: number; // e.g., in bits
  randomnessMetrics: RandomnessMetrics;
  artworkMetadata: ArtworkMetadata;
}

export interface FingerprintReport {
  randomnessExplanation: string;
  securityImplications: string;
  uniquenessAssessment: string;
  humanReadableReport: string;
  rawAIResponse?: any;
}

export interface SecurityAuditInput {
  entropyScore: number;
  randomnessMetrics: RandomnessMetrics;
  keyCharacteristics: Record<string, any>;
}

export interface SecurityAuditResult {
  weaknesses: string;
  strengths: string;
  securityQuality: string;
  summary: string;
  confidenceScore: number; // 0-1, based on data completeness
  dataCompleteness: string; // explicit note if data is missing
  rawAIResponse?: any;
}

export interface ArtworkInterpretationInput {
  generatedColors: string[] | string;
  generatedShapes: string[] | string;
  visualMetadata: Record<string, any>;
  randomnessMetrics: RandomnessMetrics;
}

export interface ArtworkInterpretationResult {
  artisticInterpretation: string;
  uniquenessExplanation: string;
  exhibitionDescription: string;
  confidenceScore: number; // 0-1, based on data completeness
  dataCompleteness: string; // explicit note if data is missing
  rawAIResponse?: any;
}

export interface ComprehensiveReportInput {
  entropyScore: number;
  randomnessMetrics: RandomnessMetrics;
  keyCharacteristics: Record<string, any>;
  generatedColors: string[] | string;
  generatedShapes: string[] | string;
  visualMetadata: Record<string, any>;
}

export interface ComprehensiveReportResult {
  report: string; // max 250 words
  wordCount: number;
  confidenceScore: number; // 0-1, based on data completeness
  dataCompleteness: string; // explicit note if data is missing
  rawAIResponse?: any;
}

export interface ExplainabilityResponse {
  entropy: string;
  randomness: string;
  uniqueness: string;
}

export interface ContextualExplainabilityResponse extends ExplainabilityResponse {
  entropyContext: string;
  randomnessContext: string;
  uniquenessContext: string;
}

export interface ConversationRequest {
  question: string;
  entropyScore?: number;
  randomnessMetrics?: Record<string, number>;
  generatedColors?: string[] | string;
  generatedShapes?: string[] | string;
  keyCharacteristics?: Record<string, any>;
}

export interface ConversationResponse {
  question: string;
  answer: string;
  category: "generation" | "uniqueness" | "security" | "entropy" | "randomness" | "other";
  demoReady: boolean;
}
