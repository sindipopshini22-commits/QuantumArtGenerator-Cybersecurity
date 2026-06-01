/**
 * ConversationalAssistant: Live Q&A for hackathon demos
 * Answers specific questions about QuantumFingerprint with concise, accurate responses.
 */

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
  demoReady: boolean; // suitable for live presentation
}

export class ConversationalAssistant {
  /**
   * Detect question category and route to appropriate handler
   */
  answerQuestion(req: ConversationRequest): ConversationResponse {
    const q = req.question.toLowerCase();

    // Question routing
    if (this.isGenerationQuestion(q)) {
      return {
        question: req.question,
        answer: this.answerGeneration(req),
        category: "generation",
        demoReady: true
      };
    }

    if (this.isUniquenessQuestion(q)) {
      return {
        question: req.question,
        answer: this.answerUniqueness(req),
        category: "uniqueness",
        demoReady: true
      };
    }

    if (this.isSecurityQuestion(q)) {
      return {
        question: req.question,
        answer: this.answerSecurity(req),
        category: "security",
        demoReady: true
      };
    }

    if (this.isEntropyQuestion(q)) {
      return {
        question: req.question,
        answer: this.answerEntropy(req),
        category: "entropy",
        demoReady: true
      };
    }

    if (this.isRandomnessQuestion(q)) {
      return {
        question: req.question,
        answer: this.answerRandomness(req),
        category: "randomness",
        demoReady: true
      };
    }

    // Fallback for unexpected questions
    return {
      question: req.question,
      answer: this.answerOther(req),
      category: "other",
      demoReady: false
    };
  }

  private isGenerationQuestion(q: string): boolean {
    return /how.*generat|generat.*how|made|creat|build|compos|render|draw|paint/i.test(q);
  }

  private isUniquenessQuestion(q: string): boolean {
    return /unique|distinct|different|special|original|never.*before|never.*seen/i.test(q);
  }

  private isSecurityQuestion(q: string): boolean {
    return /secure|safe|protect|attack|crack|hack|key.*strong|strength|vulnerable|weak/i.test(q);
  }

  private isEntropyQuestion(q: string): boolean {
    return /entropy|what.*entropy|entropy.*mean|entropy.*is/i.test(q);
  }

  private isRandomnessQuestion(q: string): boolean {
    return /random|randomness|unpredictable|predict|noise|pattern/i.test(q);
  }

  private answerGeneration(req: ConversationRequest): string {
    const colorCount = this.getColorCount(req.generatedColors);
    const shapeCount = this.getShapeCount(req.generatedShapes);

    if (colorCount === 0 || shapeCount === 0) {
      return "This artwork is generated algorithmically from a cryptographic fingerprint—a unique digital key. The algorithm maps the fingerprint's randomness data to visual properties: colors represent entropy values, and shapes represent pattern distributions. Each fingerprint produces a distinct artwork that cannot be recreated.";
    }

    return `This artwork was created by mapping your cryptographic fingerprint to visual elements. The algorithm uses ${colorCount} colors derived from your entropy data and ${shapeCount} geometric shapes from your randomness metrics. Since your fingerprint is unique, the generated composition is mathematically guaranteed to be one-of-a-kind.`;
  }

  private answerUniqueness(req: ConversationRequest): string {
    const colorCount = this.getColorCount(req.generatedColors);
    const shapeCount = this.getShapeCount(req.generatedShapes);
    const totalElements = colorCount + shapeCount;

    if (req.entropyScore && req.entropyScore > 0) {
      if (totalElements > 10) {
        return `Your artwork is unique because it's derived from your cryptographic fingerprint (entropy: ${req.entropyScore} bits). The combination of ${colorCount} colors and ${shapeCount} shapes is mathematically unique to your data. The probability of another fingerprint creating this exact design is astronomically low—essentially impossible.`;
      }
      return `Every cryptographic fingerprint is unique—like a digital fingerprint. Yours has entropy of ${req.entropyScore} bits, making it statistically unique. The visual representation with your specific colors and shapes will never be generated the same way twice. This makes your artwork both secure and unrepeatable.`;
    }

    return "Your artwork is unique because it's generated from your cryptographic fingerprint—each fingerprint produces a distinct visual composition. The algorithm converts your randomness data into colors and shapes that cannot occur by accident. This guarantees artistic originality alongside cryptographic security.";
  }

  private answerSecurity(req: ConversationRequest): string {
    const entropy = req.entropyScore || 0;

    if (entropy === 0) {
      return "Security assessment requires entropy data. Entropy measures randomness in your key. Higher entropy = stronger security and lower risk of compromise. Typical secure keys have 128–256 bits of entropy.";
    }

    if (entropy < 50) {
      return `Your key has ${entropy} bits of entropy—moderate security. This is suitable for casual protection but not for high-security applications. Consider using higher entropy sources for sensitive data.`;
    }

    if (entropy < 128) {
      return `Your key has ${entropy} bits of entropy—good security. This is suitable for most applications and provides strong resistance against guessing attacks. Your fingerprint is reliable for digital authentication.`;
    }

    return `Your key has ${entropy} bits of entropy—excellent, enterprise-grade security. This protects against virtually all guessing and brute-force attacks. Your fingerprint is suitable for the most sensitive cryptographic applications.`;
  }

  private answerEntropy(req: ConversationRequest): string {
    return "Entropy measures randomness. Think of a coin flip: you can't predict heads or tails—that's high entropy. In cryptography, high entropy means your key is impossible to guess. A truly random 256-bit key has about 256 bits of entropy, making it impossible to crack through guessing. Your system's entropy score indicates how random your fingerprint is.";
  }

  private answerRandomness(req: ConversationRequest): string {
    const metricsCount = Object.keys(req.randomnessMetrics || {}).length;

    if (metricsCount === 0) {
      return "Randomness indicates unpredictability. True randomness means no patterns can be found, making your data secure and unrepeatable. In cryptography, randomness is essential: a predictable key is a vulnerable key. Your system measures randomness through multiple statistical tests.";
    }

    const avgValue = Object.values(req.randomnessMetrics || {}).reduce((a, b) => a + b, 0) / metricsCount;

    if (avgValue > 0.9) {
      return `Your randomness metrics indicate excellent unpredictability across ${metricsCount} statistical tests. This means your fingerprint genuinely resists pattern analysis—attackers cannot predict or recreate your key. This is exactly what you want for security.`;
    }

    if (avgValue > 0.7) {
      return `Your randomness metrics show good distribution across ${metricsCount} tests. Your data demonstrates solid unpredictability suitable for cryptographic use. No hidden patterns can be exploited.`;
    }

    return `Your randomness metrics show acceptable levels across ${metricsCount} tests. Randomness ensures your fingerprint cannot be predicted or replicated, making it secure for its intended use.`;
  }

  private answerOther(req: ConversationRequest): string {
    return `I can answer questions about: How was this artwork generated? Why is it unique? How secure is the key? What does entropy mean? What does randomness indicate? Please ask one of these questions.`;
  }

  private getColorCount(colors?: string[] | string): number {
    if (!colors) return 0;
    if (Array.isArray(colors)) return colors.length;
    return colors.trim().length > 0 ? 1 : 0;
  }

  private getShapeCount(shapes?: string[] | string): number {
    if (!shapes) return 0;
    if (Array.isArray(shapes)) return shapes.length;
    return shapes.trim().length > 0 ? 1 : 0;
  }
}
