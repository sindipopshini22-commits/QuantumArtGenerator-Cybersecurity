import OpenAI from "openai";

export interface ChatMessage {
  role: "system" | "user" | "assistant";
  content: string;
}

export interface OpenAIClientOptions {
  apiKey?: string;
  model?: string;
}

export class OpenAIClient {
  private client: OpenAI;
  private model: string;

  constructor(opts: OpenAIClientOptions = {}) {
    const apiKey = opts.apiKey ?? process.env.OPENAI_API_KEY;
    this.model = opts.model ?? process.env.OPENAI_MODEL ?? "gpt-5-mini";

    if (process.env.OPENAI_MOCK === "1") {
      // In mock mode we don't initialize the real client.
      // createChatCompletion will return a canned response.
      // Set client to undefined to indicate mock mode.
      // @ts-ignore
      this.client = undefined;
      return;
    }

    if (!apiKey) throw new Error("OPENAI_API_KEY is required");
    this.client = new OpenAI({ apiKey });
  }

  async createChatCompletion(messages: ChatMessage[], temperature = 0) {
    if (process.env.OPENAI_MOCK === "1") {
      const content = messages?.map((m) => m.content).join(" ") ?? "";
      const isAudit = /weaknesses|strengths|securityQuality|summary/.test(content);
      const isArtwork = /artisticInterpretation|uniquenessExplanation|exhibitionDescription/.test(content);
      const isReport = /report|wordCount/.test(content);
      const isAnalysis = /entropyAssessment|securityAssessment|uniquenessAssessment|overallRating/.test(content);
      const responseBody = isReport
        ? {
            report:
              "QuantumFingerprint: A Digital Authenticity Standard. This generative artwork demonstrates exceptional technical merit through its integration of cryptographic fingerprinting with artistic expression. The entropy score of 98.4 bits indicates strong randomness, ensuring collision resistance and security robustness. The randomness metrics confirm algorithmic integrity, with negligible predictability. From an artistic perspective, the composition balances algorithmic generation with intentional design, where abstract color fields and dynamic geometric patterns suggest both chaos and order. The work's uniqueness stems from its dual nature: as a secure cryptographic artifact and as a compelling visual experience. The fingerprint is immutable, traceable, and reproducible only through identical inputs, making it suitable for verification and digital authenticity. Judges will recognize the sophisticated blend of security engineering and creative vision, positioning this work as a forward-thinking exploration of how cryptographic principles can inform artistic practice. Recommended for consideration in technical innovation and interdisciplinary design categories."
          }
        : isAudit
        ? {
            weaknesses:
              "The most notable weakness is the need for secure key storage and strong entropy source handling; if the key is reused or exposed, its security drops significantly.",
            strengths:
              "The key demonstrates strong randomness and entropy metrics, which reduces predictability and collision risk.",
            securityQuality:
              "Overall, the security quality appears high based on the metrics, but safe handling and lifecycle management remain important.",
            summary:
              "The audit identifies good randomness strength and key qualities, while recommending careful storage and usage practices to maintain security."
          }
        : isAnalysis
        ? {
            entropyAssessment:
              "The entropy score and randomness score both support strong randomness and low bias in the submitted key.",
            securityAssessment:
              "From the supplied metrics, the key appears secure, but storage and reuse practices should still be controlled.",
            uniquenessAssessment:
              "The fingerprint is highly unique given the entropy and randomness values, with low collision risk.",
            artisticInterpretation:
              "The digital artifact reads as a well-formed cryptographic fingerprint with strong randomness and authenticity signals.",
            overallRating: 8
          }
        : isArtwork
        ? {
            artisticInterpretation:
              "The palette and shapes suggest a dynamic, algorithmic landscape with a strong contrast between geometry and texture.",
            uniquenessExplanation:
              "The work feels distinctive because it combines randomized patterning with deliberate visual structure, making the output less predictable.",
            exhibitionDescription:
              "A generative piece that balances abstract color fields and geometric forms, inviting the viewer to explore the interplay between chance and design."
          }
        : {
            randomnessExplanation:
              "Entropy score of " + (content.match(/entropyScore:\s*(\d+\.?\d*)/)?.[1] ?? "N/A") +
              " bits indicates strong randomness for most applications. Metrics show no obvious bias.",
            securityImplications:
              "Key length and entropy are generally sufficient; avoid reuse and ensure secure storage. Rotate keys if exposed.",
            uniquenessAssessment:
              "Uniqueness appears high; collision probability is negligible based on entropy and metadata.",
            humanReadableReport:
              "This fingerprint shows strong randomness and high uniqueness. Treat the key as high-entropy and store securely."
          };

      const fake = {
        id: "mock-1",
        object: "chat.completion",
        choices: [
          {
            message: {
              role: "assistant",
              content: JSON.stringify(responseBody)
            }
          }
        ]
      };
      return fake as any;
    }

    const resp = await this.client.chat.completions.create({
      model: this.model,
      messages: messages as any,
      temperature,
      max_tokens: 1200
    });
    return resp;
  }
}
