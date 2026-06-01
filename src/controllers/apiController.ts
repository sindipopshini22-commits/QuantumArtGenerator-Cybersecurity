import { Request, Response } from "express";
import { AIService } from "../services/ai/AIService";
import { ConversationalAssistant } from "../services/ai/ConversationalAssistant";
import { ExplainabilityService } from "../services/explainability/ExplainabilityService";

const svc = new AIService();
const conversationalAssistant = new ConversationalAssistant();
const explainSvc = new ExplainabilityService();

export async function analyzeHandler(req: Request, res: Response) {
  try {
    const body = req.body;
    // Basic validation
    if (!body || typeof body.key !== "string") {
      return res.status(400).json({ error: "Invalid payload: key is required" });
    }

    const input = {
      key: body.key,
      entropy: Number(body.entropy ?? 0),
      randomnessScore: Number(body.randomnessScore ?? 0),
      metadata: body.metadata ?? {}
    };

    const result = await svc.analyzeSimple(input as any);

    return res.json({
      entropyAssessment: result.entropyAssessment,
      securityAssessment: result.securityAssessment,
      uniquenessAssessment: result.uniquenessAssessment,
      artisticInterpretation: result.artisticInterpretation,
      overallRating: result.overallRating,
      confidenceScore: result.confidenceScore,
      dataCompleteness: result.dataCompleteness
    });
  } catch (err: any) {
    console.error("analyzeHandler error:", err);
    res.status(500).json({ error: err?.message ?? String(err) });
  }
}

export async function auditHandler(req: Request, res: Response) {
  try {
    const body = req.body;
    if (!body || typeof body.entropyScore !== "number" || typeof body.randomnessMetrics !== "object") {
      return res.status(400).json({ error: "Invalid payload: entropyScore and randomnessMetrics are required" });
    }

    const input = {
      entropyScore: Number(body.entropyScore),
      randomnessMetrics: body.randomnessMetrics,
      keyCharacteristics: body.keyCharacteristics ?? {}
    };

    const result = await svc.securityAudit(input as any);

    return res.json({
      weaknesses: result.weaknesses,
      strengths: result.strengths,
      securityQuality: result.securityQuality,
      summary: result.summary,
      confidenceScore: result.confidenceScore,
      dataCompleteness: result.dataCompleteness
    });
  } catch (err: any) {
    console.error("auditHandler error:", err);
    res.status(500).json({ error: err?.message ?? String(err) });
  }
}

export async function interpretArtworkHandler(req: Request, res: Response) {
  try {
    const body = req.body;
    if (!body || (!body.generatedColors && !body.generatedShapes)) {
      return res.status(400).json({ error: "Invalid payload: generatedColors or generatedShapes are required" });
    }

    const input = {
      generatedColors: body.generatedColors,
      generatedShapes: body.generatedShapes,
      visualMetadata: body.visualMetadata ?? {},
      randomnessMetrics: body.randomnessMetrics ?? {}
    };

    const result = await svc.interpretArtwork(input as any);

    return res.json({
      artisticInterpretation: result.artisticInterpretation,
      uniquenessExplanation: result.uniquenessExplanation,
      exhibitionDescription: result.exhibitionDescription,
      confidenceScore: result.confidenceScore,
      dataCompleteness: result.dataCompleteness
    });
  } catch (err: any) {
    console.error("interpretArtworkHandler error:", err);
    res.status(500).json({ error: err?.message ?? String(err) });
  }
}

export async function generateReportHandler(req: Request, res: Response) {
  try {
    const body = req.body;
    if (!body || typeof body.entropyScore !== "number") {
      return res.status(400).json({ error: "Invalid payload: entropyScore is required" });
    }

    const input = {
      entropyScore: Number(body.entropyScore),
      randomnessMetrics: body.randomnessMetrics ?? {},
      keyCharacteristics: body.keyCharacteristics ?? {},
      generatedColors: body.generatedColors ?? [],
      generatedShapes: body.generatedShapes ?? [],
      visualMetadata: body.visualMetadata ?? {}
    };

    const result = await svc.generateComprehensiveReport(input as any);

    return res.json({
      report: result.report,
      wordCount: result.wordCount,
      confidenceScore: result.confidenceScore,
      dataCompleteness: result.dataCompleteness
    });
  } catch (err: any) {
    console.error("generateReportHandler error:", err);
    res.status(500).json({ error: err?.message ?? String(err) });
  }
}

export function explainHandler(req: Request, res: Response) {
  try {
    const explanations = explainSvc.getAllExplanations();
    return res.json(explanations);
  } catch (err: any) {
    console.error("explainHandler error:", err);
    res.status(500).json({ error: err?.message ?? String(err) });
  }
}

export function explainContextHandler(req: Request, res: Response) {
  try {
    const body = req.body;

    const entropyScore = Number(body.entropyScore ?? 0);
    const randomnessMetrics = body.randomnessMetrics ?? {};
    
    // Count colors and shapes
    let colorCount = 0;
    let shapeCount = 0;
    
    if (Array.isArray(body.generatedColors)) {
      colorCount = body.generatedColors.length;
    } else if (typeof body.generatedColors === "string") {
      colorCount = body.generatedColors.trim().length > 0 ? 1 : 0;
    }
    
    if (Array.isArray(body.generatedShapes)) {
      shapeCount = body.generatedShapes.length;
    } else if (typeof body.generatedShapes === "string") {
      shapeCount = body.generatedShapes.trim().length > 0 ? 1 : 0;
    }

    const contextualExplanations = explainSvc.getAllContextualExplanations(
      entropyScore,
      randomnessMetrics,
      colorCount,
      shapeCount
    );

    return res.json(contextualExplanations);
  } catch (err: any) {
    console.error("explainContextHandler error:", err);
    res.status(500).json({ error: err?.message ?? String(err) });
  }
}

export function conversationHandler(req: Request, res: Response) {
  try {
    const body = req.body;
    
    if (!body || typeof body.question !== "string" || body.question.trim().length === 0) {
      return res.status(400).json({ error: "Invalid payload: question is required" });
    }

    const conversationReq = {
      question: body.question,
      entropyScore: body.entropyScore ? Number(body.entropyScore) : undefined,
      randomnessMetrics: body.randomnessMetrics ?? undefined,
      generatedColors: body.generatedColors ?? undefined,
      generatedShapes: body.generatedShapes ?? undefined,
      keyCharacteristics: body.keyCharacteristics ?? undefined
    };

    const response = conversationalAssistant.answerQuestion(conversationReq);
    return res.json(response);
  } catch (err: any) {
    console.error("conversationHandler error:", err);
    res.status(500).json({ error: err?.message ?? String(err) });
  }
}
