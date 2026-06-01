import { ArtworkInterpretationInput, ArtworkInterpretationResult, ComprehensiveReportInput, ComprehensiveReportResult, FingerprintInput, FingerprintReport, SecurityAuditInput, SecurityAuditResult } from "../../models/types";
import { OpenAIClient, ChatMessage } from "../../infra/openaiClient";

export interface AnalysisResult {
  entropyAssessment: string;
  securityAssessment: string;
  uniquenessAssessment: string;
  artisticInterpretation: string;
  overallRating: number;
  confidenceScore: number; // 0-1, based on data completeness
  dataCompleteness: string; // explicit note if data is missing
  rawAIResponse?: any;
}

export class AIService {
  private client: OpenAIClient;

  constructor(client?: OpenAIClient) {
    this.client = client ?? new OpenAIClient();
  }

  private buildMessages(input: FingerprintInput): ChatMessage[] {
    const system = `You are a security-minded analyst that writes clear, concise, and structured reports about randomness, entropy, and cryptographic fingerprints. Output a JSON object with keys: randomnessExplanation, securityImplications, uniquenessAssessment, humanReadableReport.`;

    const user = `Analyze the following fingerprint input and produce the requested fields as JSON.

Input:
- cryptographicKey: ${input.cryptographicKey}
- entropyScore: ${input.entropyScore}
- randomnessMetrics: ${JSON.stringify(input.randomnessMetrics)}
- artworkMetadata: ${JSON.stringify(input.artworkMetadata)}

Guidelines:
- Explain the quality of randomness and what the entropy score implies (include any caveats).
- Explain security implications: possible attack vectors, key strength, and recommendations.
- Describe uniqueness: probability of collision, distinguishing features derived from metrics and artwork metadata.
- Provide a short human-readable report suitable for an end-user summary (2-6 sentences).

Respond only with valid JSON.`;

    return [
      { role: "system", content: system },
      { role: "user", content: user }
    ];
  }

  async generateReport(input: FingerprintInput): Promise<FingerprintReport> {
    const messages = this.buildMessages(input);
    const resp = await this.client.createChatCompletion(messages, 0);

    // Try to find assistant content
    const assistantMessage = resp?.choices?.[0]?.message?.content ?? resp?.choices?.[0]?.text;
    let parsed: any = null;
    if (assistantMessage) {
      try {
        parsed = JSON.parse(assistantMessage);
      } catch (err) {
        // Attempt to extract JSON block
        const text = assistantMessage as string;
        const jsonMatch = text.match(/\{[\s\S]*\}/);
        if (jsonMatch) {
          try {
            parsed = JSON.parse(jsonMatch[0]);
          } catch (err2) {
            parsed = null;
          }
        }
      }
    }

    if (!parsed) {
      // Fallback: create a basic report from raw text
      const fallback = (assistantMessage ?? "").toString();
      return {
        randomnessExplanation: fallback,
        securityImplications: fallback,
        uniquenessAssessment: fallback,
        humanReadableReport: fallback,
        rawAIResponse: resp
      };
    }

    const report: FingerprintReport = {
      randomnessExplanation: parsed.randomnessExplanation ?? parsed.randomness_explanation ?? "",
      securityImplications: parsed.securityImplications ?? parsed.security_implications ?? "",
      uniquenessAssessment: parsed.uniquenessAssessment ?? parsed.uniqueness_assessment ?? "",
      humanReadableReport: parsed.humanReadableReport ?? parsed.human_readable_report ?? "",
      rawAIResponse: resp
    };

    return report;
  }

  async analyzeSimple(input: {
    key: string;
    entropy: number;
    randomnessScore: number;
    metadata: Record<string, any>;
  }) {
    // Calculate data completeness
    const completenessNote = (input.entropy === 0 || !input.randomnessScore) 
      ? "Warning: Analysis based on limited entropy/randomness data."
      : "Analysis based on provided entropy and randomness scores.";
    
    const confidenceScore = (input.entropy > 0 && input.randomnessScore > 0) ? 0.8 : 0.5;

    const system = `You are a concise security analyst.

CRITICAL CONSTRAINT: Base analysis ONLY on the provided key, entropy value, and randomness score. Do not invent additional entropy values or randomness metrics not provided.
- The entropy value provided is: ${input.entropy}
- The randomness score provided is: ${input.randomnessScore}
- Use ONLY these values; do not assume or estimate different values.
- If entropy or randomness data is insufficient (values are 0 or missing), explicitly state: "Insufficient entropy/randomness data provided for complete analysis."

Return JSON with keys: entropyAssessment, securityAssessment, uniquenessAssessment, artisticInterpretation, overallRating. Keep each value as a short paragraph (1-3 sentences). Ensure overallRating is a number between 0 and 10.`;

    const user = `Input:\n- key: ${input.key}\n- entropy: ${input.entropy}\n- randomnessScore: ${input.randomnessScore}\n- metadata: ${JSON.stringify(input.metadata)}\n\n${completenessNote}\n\nRespond only with valid JSON using the exact field names.`;

    const messages: ChatMessage[] = [
      { role: "system", content: system },
      { role: "user", content: user }
    ];

    const resp = await this.client.createChatCompletion(messages, 0.0);
    const assistantMessage = resp?.choices?.[0]?.message?.content ?? resp?.choices?.[0]?.text;

    let parsed: any = null;
    if (assistantMessage) {
      try {
        parsed = JSON.parse(assistantMessage as string);
      } catch (err) {
        const text = assistantMessage as string;
        const jsonMatch = text.match(/\{[\s\S]*\}/);
        if (jsonMatch) {
          try {
            parsed = JSON.parse(jsonMatch[0]);
          } catch (err2) {
            parsed = null;
          }
        }
      }
    }

    if (!parsed) {
      const fallback = (assistantMessage ?? "").toString();
      return {
        entropyAssessment: fallback,
        securityAssessment: fallback,
        uniquenessAssessment: fallback,
        artisticInterpretation: fallback,
        overallRating: 0,
        confidenceScore: confidenceScore,
        dataCompleteness: completenessNote,
        rawAIResponse: resp
      };
    }

    const validated = this.validateAnalysisResponse(parsed, assistantMessage);
    return {
      entropyAssessment: validated.entropyAssessment,
      securityAssessment: validated.securityAssessment,
      uniquenessAssessment: validated.uniquenessAssessment,
      artisticInterpretation: validated.artisticInterpretation,
      overallRating: validated.overallRating,
      confidenceScore: confidenceScore,
      dataCompleteness: completenessNote,
      rawAIResponse: resp
    };
  }

  async securityAudit(input: SecurityAuditInput): Promise<SecurityAuditResult> {
    // Validate data completeness
    const { completenessScore, missingFields } = this.validateSecurityAuditData(input);
    const completenessNote = missingFields.length > 0 
      ? `Warning: Analysis based on incomplete data. Missing: ${missingFields.join(", ")}.`
      : "Analysis based on complete provided data.";

    const system = `You are an AI Security Auditor specializing in entropy analysis, randomness evaluation, and key authenticity.

CRITICAL CONSTRAINT: You must ONLY use the provided metrics. Do not invent, estimate, or assume values not provided.
- If randomnessMetrics is empty or insufficient, explicitly state: "Insufficient randomness data provided."
- If keyCharacteristics is empty or insufficient, explicitly state: "Insufficient key characteristics provided."
- Base all assessments ONLY on the numerical entropyScore and provided metrics.
- If you cannot make a complete assessment due to missing data, clearly state which data is needed.

Return JSON with keys: weaknesses, strengths, securityQuality, summary.`;

    const user = `Input:\n- entropyScore: ${input.entropyScore}\n- randomnessMetrics: ${JSON.stringify(input.randomnessMetrics)}\n- keyCharacteristics: ${JSON.stringify(input.keyCharacteristics)}\n\n${completenessNote}\n\nAnalyze ONLY the provided data. Return strict JSON with keys: weaknesses, strengths, securityQuality, summary.`;

    const messages: ChatMessage[] = [
      { role: "system", content: system },
      { role: "user", content: user }
    ];

    const resp = await this.client.createChatCompletion(messages, 0.0);
    const assistantMessage = resp?.choices?.[0]?.message?.content ?? resp?.choices?.[0]?.text;

    let parsed: any = null;
    if (assistantMessage) {
      try {
        parsed = JSON.parse(assistantMessage as string);
      } catch (err) {
        const text = assistantMessage as string;
        const jsonMatch = text.match(/\{[\s\S]*\}/);
        if (jsonMatch) {
          try {
            parsed = JSON.parse(jsonMatch[0]);
          } catch (err2) {
            parsed = null;
          }
        }
      }
    }

    if (!parsed) {
      const fallback = (assistantMessage ?? "").toString();
      return {
        weaknesses: fallback,
        strengths: fallback,
        securityQuality: fallback,
        summary: fallback,
        confidenceScore: completenessScore,
        dataCompleteness: completenessNote,
        rawAIResponse: resp
      };
    }

    const validated = this.validateSecurityAuditResponse(parsed, assistantMessage, completenessScore, completenessNote);
    return validated;
  }

  async interpretArtwork(input: ArtworkInterpretationInput): Promise<ArtworkInterpretationResult> {
    // Validate data completeness
    const { completenessScore, missingFields } = this.validateArtworkData(input);
    const completenessNote = missingFields.length > 0 
      ? `Warning: Analysis based on incomplete data. Missing: ${missingFields.join(", ")}.`
      : "Analysis based on complete provided data.";

    const system = `You are an AI Artwork Interpreter. 

CRITICAL CONSTRAINT: You must ONLY use the provided colors, shapes, visual metadata, and randomness metrics. Do not invent or assume visual information not provided.
- If generatedColors is empty or insufficient, explicitly state: "Insufficient color data provided."
- If generatedShapes is empty or insufficient, explicitly state: "Insufficient shape data provided."
- Base all artistic interpretation ONLY on what was actually provided.
- If you cannot make a complete artistic interpretation due to missing data, clearly state which data is needed.

Keep total output under 100 words. Return strict JSON with keys: artisticInterpretation, uniquenessExplanation, exhibitionDescription.`;

    const user = `Input:\n- generatedColors: ${JSON.stringify(input.generatedColors)}\n- generatedShapes: ${JSON.stringify(input.generatedShapes)}\n- visualMetadata: ${JSON.stringify(input.visualMetadata)}\n- randomnessMetrics: ${JSON.stringify(input.randomnessMetrics)}\n\n${completenessNote}\n\nRespond only with valid JSON using the exact field names.`;

    const messages: ChatMessage[] = [
      { role: "system", content: system },
      { role: "user", content: user }
    ];

    const resp = await this.client.createChatCompletion(messages, 0.0);
    const assistantMessage = resp?.choices?.[0]?.message?.content ?? resp?.choices?.[0]?.text;

    let parsed: any = null;
    if (assistantMessage) {
      try {
        parsed = JSON.parse(assistantMessage as string);
      } catch (err) {
        const text = assistantMessage as string;
        const jsonMatch = text.match(/\{[\s\S]*\}/);
        if (jsonMatch) {
          try {
            parsed = JSON.parse(jsonMatch[0]);
          } catch (err2) {
            parsed = null;
          }
        }
      }
    }

    if (!parsed) {
      const fallback = (assistantMessage ?? "").toString();
      return {
        artisticInterpretation: fallback,
        uniquenessExplanation: fallback,
        exhibitionDescription: fallback,
        confidenceScore: completenessScore,
        dataCompleteness: completenessNote,
        rawAIResponse: resp
      };
    }

    const validated = this.validateArtworkResponse(parsed, assistantMessage, completenessScore, completenessNote);
    return validated;
  }

  async generateComprehensiveReport(input: ComprehensiveReportInput): Promise<ComprehensiveReportResult> {
    // Validate data completeness
    const { completenessScore, missingFields } = this.validateComprehensiveReportData(input);
    const completenessNote = missingFields.length > 0 
      ? `Note: Report based on incomplete data. Missing: ${missingFields.join(", ")}.`
      : "Report based on complete provided data.";

    const system = `You are a professional report writer for hackathon judges. 

CRITICAL CONSTRAINT: Base this report ONLY on the provided entropy score, randomness metrics, key characteristics, colors, and shapes. Do not invent or assume metrics not provided.
- If critical data is missing (e.g., entropy score is 0, randomness metrics empty), acknowledge this limitation in the report.
- Use precise technical language while maintaining accessibility.
- Structure: introduce the fingerprint, explain randomness quality using only provided metrics, assess security implications based only on provided data, describe artistic uniqueness based only on provided colors/shapes, and conclude with overall significance.

Generate a professional report under 250 words.`;

    const user = `Input:\n- entropyScore: ${input.entropyScore}\n- randomnessMetrics: ${JSON.stringify(input.randomnessMetrics)}\n- keyCharacteristics: ${JSON.stringify(input.keyCharacteristics)}\n- generatedColors: ${JSON.stringify(input.generatedColors)}\n- generatedShapes: ${JSON.stringify(input.generatedShapes)}\n- visualMetadata: ${JSON.stringify(input.visualMetadata)}\n\n${completenessNote}\n\nGenerate a professional report under 250 words. Return JSON with key "report".`;

    const messages: ChatMessage[] = [
      { role: "system", content: system },
      { role: "user", content: user }
    ];

    const resp = await this.client.createChatCompletion(messages, 0.2);
    const assistantMessage = resp?.choices?.[0]?.message?.content ?? resp?.choices?.[0]?.text;

    let parsed: any = null;
    if (assistantMessage) {
      try {
        parsed = JSON.parse(assistantMessage as string);
      } catch (err) {
        const text = assistantMessage as string;
        const jsonMatch = text.match(/\{[\s\S]*\}/);
        if (jsonMatch) {
          try {
            parsed = JSON.parse(jsonMatch[0]);
          } catch (err2) {
            parsed = null;
          }
        }
      }
    }

    const reportText = parsed?.report ?? parsed?.text ?? (assistantMessage as string);
    const wordCount = (reportText ?? "").split(/\s+/).filter((w: string) => w.length > 0).length;

    return {
      report: reportText,
      wordCount,
      confidenceScore: completenessScore,
      dataCompleteness: completenessNote,
      rawAIResponse: resp
    };
  }

  private validateArtworkResponse(parsed: any, assistantMessage: string | undefined, completenessScore: number, completenessNote: string): ArtworkInterpretationResult {
    const result: Partial<ArtworkInterpretationResult> = {
      artisticInterpretation: parsed.artisticInterpretation ?? parsed.artistic_interpretation,
      uniquenessExplanation: parsed.uniquenessExplanation ?? parsed.uniqueness_explanation,
      exhibitionDescription: parsed.exhibitionDescription ?? parsed.exhibition_description
    };

    const fallback = (assistantMessage ?? "").toString();
    return {
      artisticInterpretation: typeof result.artisticInterpretation === "string" ? result.artisticInterpretation : fallback,
      uniquenessExplanation: typeof result.uniquenessExplanation === "string" ? result.uniquenessExplanation : fallback,
      exhibitionDescription: typeof result.exhibitionDescription === "string" ? result.exhibitionDescription : fallback,
      confidenceScore: completenessScore,
      dataCompleteness: completenessNote,
      rawAIResponse: undefined
    };
  }

  private validateSecurityAuditResponse(parsed: any, assistantMessage: string | undefined, completenessScore: number, completenessNote: string): SecurityAuditResult {
    const result: Partial<SecurityAuditResult> = {
      weaknesses: parsed.weaknesses ?? parsed.weaknesses,
      strengths: parsed.strengths ?? parsed.strengths,
      securityQuality: parsed.securityQuality ?? parsed.security_quality,
      summary: parsed.summary
    };

    const fallback = (assistantMessage ?? "").toString();
    return {
      weaknesses: typeof result.weaknesses === "string" ? result.weaknesses : fallback,
      strengths: typeof result.strengths === "string" ? result.strengths : fallback,
      securityQuality: typeof result.securityQuality === "string" ? result.securityQuality : fallback,
      summary: typeof result.summary === "string" ? result.summary : fallback,
      confidenceScore: completenessScore,
      dataCompleteness: completenessNote,
      rawAIResponse: undefined
    };
  }

  private validateAnalysisResponse(parsed: any, assistantMessage: string | undefined): AnalysisResult {
    const result: Partial<AnalysisResult> = {
      entropyAssessment: parsed.entropyAssessment ?? parsed.entropy_assessment,
      securityAssessment: parsed.securityAssessment ?? parsed.security_assessment,
      uniquenessAssessment: parsed.uniquenessAssessment ?? parsed.uniqueness_assessment,
      artisticInterpretation: parsed.artisticInterpretation ?? parsed.artistic_interpretation,
      overallRating: typeof parsed.overallRating === "number" ? parsed.overallRating : parsed.overall_rating
    };

    const fallback = (assistantMessage ?? "").toString();

    return {
      entropyAssessment: typeof result.entropyAssessment === "string" ? result.entropyAssessment : fallback,
      securityAssessment: typeof result.securityAssessment === "string" ? result.securityAssessment : fallback,
      uniquenessAssessment: typeof result.uniquenessAssessment === "string" ? result.uniquenessAssessment : fallback,
      artisticInterpretation: typeof result.artisticInterpretation === "string" ? result.artisticInterpretation : fallback,
      overallRating: typeof result.overallRating === "number" ? result.overallRating : 0,
      confidenceScore: 1.0, // Placeholder for analyzeSimple (legacy, not using data validation)
      dataCompleteness: "Analysis based on provided input.",
      rawAIResponse: undefined
    };
  }

  private validateSecurityAuditData(input: SecurityAuditInput): { completenessScore: number; missingFields: string[] } {
    const missing: string[] = [];
    
    if (!input.entropyScore || input.entropyScore === 0) {
      missing.push("entropyScore");
    }
    
    if (!input.randomnessMetrics || Object.keys(input.randomnessMetrics).length === 0) {
      missing.push("randomnessMetrics");
    }
    
    if (!input.keyCharacteristics || Object.keys(input.keyCharacteristics).length === 0) {
      missing.push("keyCharacteristics");
    }
    
    // Confidence: 1.0 = complete, 0.5 = ~50% complete, 0.0 = critical data missing
    const completenessScore = Math.max(0, 1.0 - (missing.length * 0.33));
    
    return { completenessScore, missingFields: missing };
  }

  private validateArtworkData(input: ArtworkInterpretationInput): { completenessScore: number; missingFields: string[] } {
    const missing: string[] = [];
    
    const hasColors = input.generatedColors && (Array.isArray(input.generatedColors) ? input.generatedColors.length > 0 : input.generatedColors.length > 0);
    const hasShapes = input.generatedShapes && (Array.isArray(input.generatedShapes) ? input.generatedShapes.length > 0 : input.generatedShapes.length > 0);
    
    if (!hasColors) {
      missing.push("generatedColors");
    }
    
    if (!hasShapes) {
      missing.push("generatedShapes");
    }
    
    if (!input.visualMetadata || Object.keys(input.visualMetadata).length === 0) {
      missing.push("visualMetadata");
    }
    
    if (!input.randomnessMetrics || Object.keys(input.randomnessMetrics).length === 0) {
      missing.push("randomnessMetrics");
    }
    
    const completenessScore = Math.max(0, 1.0 - (missing.length * 0.25));
    
    return { completenessScore, missingFields: missing };
  }

  private validateComprehensiveReportData(input: ComprehensiveReportInput): { completenessScore: number; missingFields: string[] } {
    const missing: string[] = [];
    
    if (!input.entropyScore || input.entropyScore === 0) {
      missing.push("entropyScore");
    }
    
    if (!input.randomnessMetrics || Object.keys(input.randomnessMetrics).length === 0) {
      missing.push("randomnessMetrics");
    }
    
    if (!input.keyCharacteristics || Object.keys(input.keyCharacteristics).length === 0) {
      missing.push("keyCharacteristics");
    }
    
    const hasColors = input.generatedColors && (Array.isArray(input.generatedColors) ? input.generatedColors.length > 0 : input.generatedColors.length > 0);
    if (!hasColors) {
      missing.push("generatedColors");
    }
    
    const hasShapes = input.generatedShapes && (Array.isArray(input.generatedShapes) ? input.generatedShapes.length > 0 : input.generatedShapes.length > 0);
    if (!hasShapes) {
      missing.push("generatedShapes");
    }
    
    if (!input.visualMetadata || Object.keys(input.visualMetadata).length === 0) {
      missing.push("visualMetadata");
    }
    
    const completenessScore = Math.max(0, 1.0 - (missing.length * 0.14)); // ~7 critical fields
    
    return { completenessScore, missingFields: missing };
  }
}
