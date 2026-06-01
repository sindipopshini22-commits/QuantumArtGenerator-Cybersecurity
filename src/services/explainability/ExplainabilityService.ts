/**
 * ExplainabilityService: Provides non-technical explanations for non-expert users.
 * All explanations target a general audience and stay under 150 words.
 */

export interface Explanations {
  entropy: string;
  randomness: string;
  uniqueness: string;
}

export interface ContextualExplanations extends Explanations {
  entropyContext: string;        // tailored to user's actual entropy score
  randomnessContext: string;     // tailored to user's randomness data
  uniquenessContext: string;     // tailored to user's artwork
}

export class ExplainabilityService {
  /**
   * Generic explanation: What is entropy?
   * Non-technical, ~120 words
   */
  getEntropyExplanation(): string {
    return `Entropy is a measure of how unpredictable or "random" something is. Think of it like this: if you flip a coin, you can't know if it'll land on heads or tails—that's high entropy. But if you flip a coin rigged to always land on heads, that's low entropy because you can predict the outcome.

In cryptography, entropy measures how difficult it is to guess a digital key or fingerprint. High entropy means the key is very hard to guess or reproduce by accident. So when we say your fingerprint has high entropy, it means your digital signature is unique and nearly impossible to duplicate through pure chance.

Higher entropy = stronger security and less risk of accidental collision.`;
  }

  /**
   * Generic explanation: Why does randomness matter?
   * Non-technical, ~130 words
   */
  getRandomnessExplanation(): string {
    return `Randomness matters because the harder something is to predict, the safer it is. Imagine a lock that uses a predictable code—a thief could guess it. But a lock with a truly random code is nearly impossible to crack by guessing.

Digital systems need randomness for security. When generating cryptographic fingerprints, random patterns make each fingerprint unique and impossible to forge. Without good randomness, attackers could duplicate your keys or create fake copies that look legitimate.

In your artwork, randomness creates the unpredictable visual patterns that make it distinctive. The more truly random the generation process, the less likely someone could recreate your exact design. This randomness is what makes your fingerprint both secure and artistically original.`;
  }

  /**
   * Generic explanation: Why is the artwork unique?
   * Non-technical, ~140 words
   */
  getArtworkUniquenessExplanation(): string {
    return `Your generated artwork is unique because it's created from a truly random cryptographic fingerprint—like a digital snowflake. No two snowflakes ever form identically, and no two randomly-generated fingerprints do either.

The colors, shapes, and patterns in your artwork are algorithmically derived from your cryptographic data. Since that data is unique to you, the visual output is also one-of-a-kind. Even if someone tried to recreate it perfectly, they'd need your exact same fingerprint, which is virtually impossible.

This uniqueness serves two purposes: it makes your artwork visually distinct and unrepeatable, and it ensures your digital fingerprint is authenticated and traceable only to you. The randomness guarantees both artistic originality and cryptographic security.`;
  }

  /**
   * Contextual entropy explanation based on actual entropy score
   */
  getContextualEntropyExplanation(entropyScore: number): string {
    if (entropyScore === 0) {
      return `Your fingerprint currently has no entropy score recorded. To understand your fingerprint's security strength, we need to measure its randomness level.`;
    }
    
    if (entropyScore < 50) {
      return `Your entropy score of ${entropyScore} bits indicates moderate randomness. For perspective, this means your fingerprint has some good unpredictability, but adding more random data would strengthen it further. Think of it like a lock with a decent-length code—secure for casual protection, but stronger codes are better for sensitive data.`;
    }
    
    if (entropyScore < 128) {
      return `Your entropy score of ${entropyScore} bits shows strong randomness. This means your fingerprint is very hard to guess or duplicate accidentally. It's like having a strong, complex password—very unlikely to be cracked through guessing alone. This level of entropy is suitable for most digital security applications.`;
    }
    
    return `Your entropy score of ${entropyScore} bits indicates excellent randomness—enterprise-grade security. Your fingerprint is nearly impossible to compromise through guessing or chance duplication. This level of entropy is used to protect the most sensitive data and is suitable for high-security applications.`;
  }

  /**
   * Contextual randomness explanation based on provided metrics
   */
  getContextualRandomnessExplanation(randomnessMetrics: Record<string, number>): string {
    const metricsCount = Object.keys(randomnessMetrics).length;
    
    if (metricsCount === 0) {
      return `We don't yet have randomness metrics for your fingerprint. Randomness metrics measure different statistical properties to verify your data is truly unpredictable. These might include distribution tests, entropy calculations, and compression analysis.`;
    }

    const avgValue = Object.values(randomnessMetrics).reduce((a, b) => a + b, 0) / metricsCount;
    
    if (avgValue > 0.9) {
      return `Your randomness metrics show excellent distribution patterns. Your fingerprint passes multiple statistical tests for true randomness. This means your data genuinely lacks patterns that could be exploited, making it highly suitable for cryptographic applications and secure authentication.`;
    }
    
    if (avgValue > 0.7) {
      return `Your randomness metrics indicate good randomness across multiple measures. Your fingerprint shows solid unpredictability patterns, suitable for most security applications. The data resists attempts to find hidden patterns or predict future values.`;
    }
    
    return `Your randomness metrics show acceptable randomness levels, though there's room for improvement. Consider enriching your input data with additional noise sources or using more bits to strengthen randomness characteristics.`;
  }

  /**
   * Contextual uniqueness explanation based on artwork attributes
   */
  getContextualUniquenessExplanation(colorCount: number, shapeCount: number): string {
    const totalElements = colorCount + shapeCount;
    
    if (totalElements === 0) {
      return `Your artwork hasn't been generated yet, so we can't explain its uniqueness. Once created, the combination of your specific colors and shapes will form a one-of-a-kind visual signature derived from your cryptographic fingerprint.`;
    }
    
    if (totalElements < 5) {
      return `Your artwork uses ${colorCount} colors and ${shapeCount} shapes. While this creates a distinctive design, it represents a limited visual palette. Adding more color and shape variety would increase the artistic complexity and visual uniqueness of your fingerprint representation.`;
    }
    
    if (totalElements < 15) {
      return `Your artwork combines ${colorCount} colors with ${shapeCount} shapes, creating a moderately complex visual composition. This variety ensures your design stands out from simple patterns while remaining visually cohesive. The combination is likely to be distinctive and hard to accidentally replicate.`;
    }
    
    return `Your artwork is highly complex with ${colorCount} colors and ${shapeCount} shapes. This elaborate combination virtually guarantees your visual fingerprint is unique—the probability of someone creating this exact design through random generation is astronomically low.`;
  }

  /**
   * Get all generic explanations at once
   */
  getAllExplanations(): Explanations {
    return {
      entropy: this.getEntropyExplanation(),
      randomness: this.getRandomnessExplanation(),
      uniqueness: this.getArtworkUniquenessExplanation()
    };
  }

  /**
   * Get all contextual explanations at once
   */
  getAllContextualExplanations(
    entropyScore: number,
    randomnessMetrics: Record<string, number>,
    colorCount: number,
    shapeCount: number
  ): ContextualExplanations {
    return {
      entropy: this.getEntropyExplanation(),
      randomness: this.getRandomnessExplanation(),
      uniqueness: this.getArtworkUniquenessExplanation(),
      entropyContext: this.getContextualEntropyExplanation(entropyScore),
      randomnessContext: this.getContextualRandomnessExplanation(randomnessMetrics),
      uniquenessContext: this.getContextualUniquenessExplanation(colorCount, shapeCount)
    };
  }
}
