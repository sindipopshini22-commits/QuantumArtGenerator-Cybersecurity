import express from "express";
import cors from "cors";
import { analyzeHandler, auditHandler, interpretArtworkHandler, generateReportHandler, explainHandler, explainContextHandler, conversationHandler } from "./controllers/apiController";

const app = express();
const port = process.env.PORT ? Number(process.env.PORT) : 3000;

app.use(cors());
app.use(express.json());

app.post("/api/analyze", analyzeHandler);
app.post("/api/audit", auditHandler);
app.post("/api/artwork", interpretArtworkHandler);
app.post("/api/report", generateReportHandler);
app.get("/api/explain", explainHandler);
app.post("/api/explain-context", explainContextHandler);
app.post("/api/chat", conversationHandler);
app.get("/api/chat", (req, res) => {
  res.json({
    ok: true,
    route: "/api/chat",
    method: "GET",
    message: "Use POST /api/chat with { question } to start a conversation."
  });
});

app.get("/", (req, res) => res.json({ ok: true }));

app.listen(port, () => {
  console.log(`QuantumFingerprint AI API listening on http://localhost:${port}`);
});
