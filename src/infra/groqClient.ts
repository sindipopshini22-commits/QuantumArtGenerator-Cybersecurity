import Groq from "groq-sdk";

export interface ChatMessage {
  role: "system" | "user" | "assistant";
  content: string;
}

export interface GroqClientOptions {
  apiKey?: string;
  model?: string;
}

export class GroqClient {
  private client: Groq | undefined;
  private model: string;

  constructor(opts: GroqClientOptions = {}) {
    const apiKey = opts.apiKey ?? process.env.GROQ_API_KEY;
    this.model = opts.model ?? process.env.GROQ_MODEL ?? "llama-3.1-8b-instant";

    if (process.env.OPENAI_MOCK === "1") {
      this.client = undefined;
      return;
    }

    if (!apiKey) {
      console.warn("GROQ_API_KEY not set - running in mock mode");
      this.client = undefined;
      return;
    }
    this.client = new Groq({ apiKey });
  }

  async createChatCompletion(messages: ChatMessage[], temperature = 0) {
    if (!this.client) {
      const content = messages?.map((m) => m.content).join(" ") ?? "";

      // More specific patterns to avoid false matches
      const isAudit = /"weaknesses"/.test(content) || /"strengths"/.test(content);
      const isArtwork = /"artisticInterpretation"/.test(content) || /"exhibitionDescription"/.test(content);
      const isComprehensiveReport = /Generate a professional report/.test(content);
      const isAnalysis = /"entropyAssessment"/.test(content) && /"overallRating"/.test(content);
      const isFingerprintReport = /"randomnessExplanation"/.test(content);

      let responseBody: any;
      if (isComprehensiveReport) {
        responseBody = {
          report:
            "QuantumFingerprint: A Digital Authenticity Standard. This generative artwork demonstrates exceptional technical merit through its integration of cryptographic fingerprinting with artistic expression. The entropy score indicates strong randomness, ensuring collision resistance and security robustness. The randomness metrics confirm algorithmic integrity, with negligible predictability. From an artistic perspective, the composition balances algorithmic generation with intentional design, where abstract color fields and dynamic geometric patterns suggest both chaos and order. The work's uniqueness stems from its dual nature: as a secure cryptographic artifact and as a compelling visual experience. The fingerprint is immutable, traceable, and reproducible only through identical inputs, making it suitable for verification and digital authenticity."
        };
      } else if (isAudit) {
        responseBody = {
          weaknesses:
            "The most notable weakness is the need for secure key storage and strong entropy source handling; if the key is reused or exposed, its security drops significantly.",
          strengths:
            "The key demonstrates strong randomness and entropy metrics, which reduces predictability and collision risk.",
          securityQuality:
            "Overall, the security quality appears high based on the metrics, but safe handling and lifecycle management remain important.",
          summary:
            "The audit identifies good randomness strength and key qualities, while recommending careful storage and usage practices to maintain security."
        };
      } else if (isAnalysis) {
        responseBody = {
          entropyAssessment:
            "The entropy score and randomness score both support strong randomness and low bias in the submitted key.",
          securityAssessment:
            "From the supplied metrics, the key appears secure, but storage and reuse practices should still be controlled.",
          uniquenessAssessment:
            "The fingerprint is highly unique given the entropy and randomness values, with low collision risk.",
          artisticInterpretation:
            "The digital artifact reads as a well-formed cryptographic fingerprint with strong randomness and authenticity signals.",
          overallRating: 8
        };
      } else if (isArtwork) {
        responseBody = {
          artisticInterpretation:
            "The palette and shapes suggest a dynamic, algorithmic landscape with a strong contrast between geometry and texture.",
          uniquenessExplanation:
            "The work feels distinctive because it combines randomized patterning with deliberate visual structure, making the output less predictable.",
          exhibitionDescription:
            "A generative piece that balances abstract color fields and geometric forms, inviting the viewer to explore the interplay between chance and design."
        };
      } else {
        responseBody = {
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
      }

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