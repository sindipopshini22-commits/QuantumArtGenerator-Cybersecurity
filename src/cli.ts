import { generateReport } from "./controllers/reportController";

async function main() {
  const sample = {
    cryptographicKey: "a1b2c3d4e5f6...",
    entropyScore: 112.4,
    randomnessMetrics: {
      chiSquared: 0.98,
      frequencyMonobit: 0.49,
      serialCorrelation: 0.01
    },
    artworkMetadata: {
      title: "Quantum Bloom",
      artist: "Ana Q.",
      creationDate: "2026-05-30",
      attributes: { style: "generative", palette: "vibrant" }
    }
  };

  try {
    const report = await generateReport(sample as any);
    console.log("--- Human-readable report ---\n", report.humanReadableReport);
    console.log("--- Full structured report ---\n", JSON.stringify(report, null, 2));
  } catch (err) {
    console.error("Error generating report:", err);
  }
}

main();
