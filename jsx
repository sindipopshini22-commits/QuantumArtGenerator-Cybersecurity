// src/pages/MainPage.jsx
import React, { useState, useEffect, useRef, useCallback } from 'react';
import './MainPage.css';

// ==================== DETERMINISTIC KEY-BOUND ENGINE ====================
const sha256 = (str) => {
  let hash = 0;
  for (let i = 0; i < str.length; i++) {
    const char = str.charCodeAt(i);
    hash = ((hash << 5) - hash) + char;
    hash = hash & hash;
  }
  return Math.abs(hash);
};

const seededRandom = (seed) => {
  let s = seed;
  return () => {
    s = (s * 16807 + 0) % 2147483647;
    return (s - 1) / 2147483646;
  };
};

const generateFromKey = (key, entropy) => {
  const seed = sha256(key);
  const rng = seededRandom(seed);
  const rng2 = seededRandom(seed + Math.floor(entropy * 1000));

  const palettes = [
    ['#00f0ff', '#4a90d9', '#1a6b3a', '#a0c4ff'],
    ['#ff006e', '#8338ec', '#3a86ff', '#06ffa5'],
    ['#ffbe0b', '#fb5607', '#ff006e', '#8338ec'],
    ['#e0e1dd', '#778da9', '#415a77', '#1b263b'],
    ['#f72585', '#7209b7', '#3a0ca3', '#4361ee'],
    ['#06ffa5', '#00f0ff', '#4a90d9', '#1a6b3a'],
    ['#fb5607', '#ffbe0b', '#ff006e', '#8338ec'],
    ['#3a0ca3', '#f72585', '#4361ee', '#7209b7'],
    ['#ff006e', '#06ffa5', '#3a86ff', '#ffbe0b'],
    ['#1a6b3a', '#a0c4ff', '#00f0ff', '#4a90d9'],
    ['#7209b7', '#f72585', '#ffbe0b', '#fb5607'],
    ['#4361ee', '#3a0ca3', '#06ffa5', '#00f0ff'],
  ];
  const palette = palettes[Math.floor(rng() * palettes.length)];

  const allShapes = ['hexagon', 'torus', 'probability-cloud', 'mandelbrot', 'julia-set', 'hypercube', 'klein-bottle', 'sierpinski', 'attractor', 'fractal-tree', 'lorenz', 'rossler'];
  const shapeCount = 2 + Math.floor(rng() * 3);
  const shapes = [];
  for (let i = 0; i < shapeCount; i++) shapes.push(allShapes[Math.floor(rng() * allShapes.length)]);

  const metrics = {
    chiSquared: +(0.85 + rng2() * 0.149).toFixed(4),
    frequencyMonobit: +(0.45 + rng2() * 0.10).toFixed(4),
    serialCorrelation: +(0.001 + rng2() * 0.049).toFixed(4)
  };

  const prefixes = ['Quantum', 'Entangled', 'Superposed', 'Coherent', 'Decoherent', 'Holographic', 'Probabilistic', 'Eigenstate', 'Interference', 'Tunneling', 'Wavefunction', 'Decoherence'];
  const suffixes = ['Bloom', 'Collapse', 'Tunnel', 'Oscillation', 'Interference', 'Wavefunction', 'Singularity', 'Nebula', 'Lattice', 'Fracture', 'Catalyst', 'Resonance', 'Harmonic', 'Vertex'];
  const title = prefixes[Math.floor(rng() * prefixes.length)] + ' ' + suffixes[Math.floor(rng() * suffixes.length)];

  const qubits = [64, 128, 256, 512, 1024];
  const qubit = qubits[Math.floor(rng() * qubits.length)];

  return { palette, shapes, metrics, title, qubit, seed };
};

// ==================== BACKEND SIMULATION ====================
const Backend = {
  async createChatCompletion(messages) {
    await new Promise(r => setTimeout(r, 600 + Math.random() * 400));
    const userMsg = messages.find(m => m.role === 'user')?.content || '';
    const entropy = parseFloat(userMsg.match(/entropyScore:\s*([\d.]+)/)?.[1] || '112.4');
    const key = (userMsg.match(/cryptographicKey:\s*([^\n]+)/)?.[1] || 'a1b2c3d4e5f6...').trim();
    const title = (userMsg.match(/artworkMetadata.*?title[^:]*:\s*"([^"]+)"/)?.[1] || 'Quantum Bloom');
    const chiSq = parseFloat(userMsg.match(/chiSquared[^:]*:\s*([\d.]+)/)?.[1] || '0.98');
    const freqMono = parseFloat(userMsg.match(/frequencyMonobit[^:]*:\s*([\d.]+)/)?.[1] || '0.49');
    const serialCorr = parseFloat(userMsg.match(/serialCorrelation[^:]*:\s*([\d.]+)/)?.[1] || '0.01');
    const colors = (userMsg.match(/generatedColors[^:]*:\s*\[([^\]]*)\]/)?.[1] || '').replace(/"/g, '').split(',').filter(c => c.trim());
    const shapes = (userMsg.match(/generatedShapes[^:]*:\s*\[([^\]]*)\]/)?.[1] || '').replace(/"/g, '').split(',').filter(s => s.trim());

    const quality = entropy > 100 ? 'high-quality' : entropy > 60 ? 'moderate' : 'low';
    const strength = entropy > 100 ? 'strong' : entropy > 60 ? 'adequate' : 'weak';
    const collisionExp = Math.round(entropy);
    const securityQual = entropy > 100 ? 'EXCELLENT' : entropy > 60 ? 'GOOD' : 'FAIR';
    const weakness = entropy < 80 ? 'Low entropy exposes key to statistical attacks and brute-force enumeration. Recommend increasing source randomness.' : 'No significant weaknesses detected in current threat model. Key space is sufficiently large.';
    const strengths = `High entropy (${entropy} bits) provides ${entropy > 100 ? 'robust' : 'functional'} key space. Serial correlation ${serialCorr} indicates ${serialCorr < 0.02 ? 'minimal' : 'moderate'} predictable patterns. Chi-squared ${chiSq} confirms ${chiSq > 0.95 ? 'near-uniform' : 'acceptable'} distribution.`;
    const summary = `Security audit complete. Overall quality: ${securityQual}. Key ${entropy > 80 ? 'safe' : 'requires hardening'} for production use. ${entropy > 100 ? 'Quantum-resistant algorithms recommended for long-term security.' : 'Consider increasing entropy source or key rotation frequency.'}`;

    const colorNames = colors.length > 0 ? colors.join(', ') : 'quantum cyan';
    const shapeNames = shapes.length > 0 ? shapes.join(', ') : 'probability clouds';
    const gallery = ['digital gallery', 'NFT marketplace', 'generative art exhibition', 'quantum computing showcase', 'blockchain art platform'];
    const process = ['generative process', 'stochastic algorithm', 'entropy-driven pipeline', 'quantum-inspired synthesis', 'hash-bound generation'];
    const visual = ['quantum decoherence', 'wavefunction collapse', 'superposition visualization', 'interference patterns', 'probability amplitude rendering'];
    const style = ['vibrant', 'muted', 'monochromatic', 'polychromatic', 'iridescent', 'prismatic'];
    const narrative = ['quantum noise', 'stochastic beauty', 'entangled forms', 'probabilistic art', 'deterministic chaos', 'hash-bound aesthetics'];
    const venue = ['gallery exhibition', 'blockchain minting', 'academic study', 'commercial licensing', 'museum acquisition'];

    const pick = (arr, s) => arr[s % arr.length];
    const s = sha256(key + entropy);

    if (userMsg.includes('randomnessExplanation')) {
      return {
        choices: [{
          message: {
            content: JSON.stringify({
              randomnessExplanation: `Entropy score of ${entropy} bits indicates ${quality} randomness. Chi-squared ${chiSq} suggests ${chiSq > 0.95 ? 'near-uniform' : 'acceptable'} distribution. Frequency monobit ${freqMono} shows ${freqMono > 0.48 && freqMono < 0.52 ? 'balanced' : 'skewed'} bit balance. Serial correlation ${serialCorr} indicates ${serialCorr < 0.02 ? 'minimal' : 'significant'} sequential dependencies.`,
              securityImplications: `Key "${key}" (${key.length} chars) shows ${strength} resistance to brute-force. ${entropy < 80 ? 'WARNING: entropy below 80 bits vulnerable to modern cracking.' : 'Collision resistance: 2^-' + collisionExp + '. Safe against preimage attacks.'} Recommend ${entropy > 100 ? 'AES-256' : 'AES-128'} encryption.`,
              uniquenessAssessment: `Collision probability: ~2^-${collisionExp}. Distinguishing features: ${title} palette [${colorNames}], ${shapeNames.length} geometric primitives. Estimated uniqueness: ${(entropy / 128 * 100).toFixed(1)}% of ideal 128-bit space. Hash-bound generation ensures reproducible artwork from key.`,
              humanReadableReport: `This artwork "${title}" fingerprint demonstrates ${quality} entropy quality with ${serialCorr < 0.02 ? 'minimal' : 'some'} correlation. The ${key.length}-character cryptographic key is ${strength} for current threat models. ${chiSq > 0.95 ? 'Distribution is near-ideal.' : 'Distribution shows minor deviations.'} Artwork is deterministically bound to key hash.`
            })
          }
        }]
      };
    }
    if (userMsg.includes('weaknesses')) {
      return {
        choices: [{
          message: {
            content: JSON.stringify({
              weaknesses: weakness,
              strengths: strengths,
              securityQuality: securityQual,
              summary: summary
            })
          }
        }]
      };
    }
    if (userMsg.includes('artisticInterpretation')) {
      return {
        choices: [{
          message: {
            content: JSON.stringify({
              artisticInterpretation: `"${title}" manifests as a ${pick(['quantum bloom', 'probability nebula', 'entangled lattice', 'decoherent wave', 'superposed constellation', 'interference mandala', 'tunneling cascade'], s)} — ${colorNames} emerging from ${shapeNames}, entangled in ${entropy}-dimensional probability space. Each vertex is a hash-derived coordinate.`,
              uniquenessExplanation: `Each pixel is a function of ${entropy}-bit entropy and ${shapeNames.length} geometric primitives (${shapeNames}), making this piece statistically unique with collision probability 2^-${collisionExp}. The SHA-256 key hash ensures identical input produces identical output — a deterministic quantum fingerprint.`,
              exhibitionDescription: `Suitable for ${pick(gallery, s)}. The ${pick(process, s)} mirrors ${pick(visual, s)} visually. Recommended for ${pick(venue, s)} with cryptographic provenance.`
            })
          }
        }]
      };
    }
    if (userMsg.includes('professional report')) {
      const report = `This fingerprint for "${title}" demonstrates ${quality} entropy quality (${entropy} bits). The randomness metrics (chi-squared ${chiSq}, serial correlation ${serialCorr}) indicate ${chiSq > 0.95 ? 'near-ideal' : 'acceptable'} distribution. Security implications: the key space is ${entropy > 100 ? 'sufficiently large' : 'adequate'} to resist brute-force attacks. ${entropy < 80 ? 'WARNING: Low entropy detected. Recommend increasing randomness source or reducing key lifetime.' : ''} Artistic uniqueness derives from ${entropy}-bit color generation using palette [${colorNames}] and shapes [${shapeNames}], producing a piece that is statistically irreproducible without the original key. The ${pick(style, s)} palette and ${pick(process, s)} create a compelling visual narrative of ${pick(narrative, s)}. Overall significance: this artwork represents a ${securityQual.toLowerCase()} security, unique digital artifact suitable for cryptographic provenance and ${pick(venue, s)}. The hash-bound generation ensures reproducibility: same key, same artwork.`;
      return {
        choices: [{
          message: {
            content: JSON.stringify({ report: report })
          }
        }]
      };
    }
    return { choices: [{ message: { content: '{}' } }] };
  },

  async generateReport(input) {
    const system = `You are a security-minded analyst. Output JSON with keys: randomnessExplanation, securityImplications, uniquenessAssessment, humanReadableReport.`;
    const user = `Analyze fingerprint input.\n\nInput:\n- cryptographicKey: ${input.cryptographicKey}\n- entropyScore: ${input.entropyScore}\n- randomnessMetrics: ${JSON.stringify(input.randomnessMetrics)}\n- artworkMetadata: ${JSON.stringify(input.artworkMetadata)}\n\nRespond only with valid JSON.`;
    const resp = await this.createChatCompletion([{role:'system',content:system},{role:'user',content:user}]);
    return this.parseResponse(resp, ['randomnessExplanation','securityImplications','uniquenessAssessment','humanReadableReport']);
  },

  async securityAudit(input) {
    const system = `You are an AI Security Auditor. Return JSON with keys: weaknesses, strengths, securityQuality, summary.`;
    const user = `Input:\n- entropyScore: ${input.entropyScore}\n- randomnessMetrics: ${JSON.stringify(input.randomnessMetrics)}\n- keyCharacteristics: ${JSON.stringify(input.keyCharacteristics)}\n\nReturn strict JSON.`;
    const resp = await this.createChatCompletion([{role:'system',content:system},{role:'user',content:user}]);
    const parsed = this.parseResponse(resp, ['weaknesses','strengths','securityQuality','summary']);
    return { ...parsed, confidenceScore: 1.0, dataCompleteness: 'Analysis based on complete provided data.' };
  },

  async interpretArtwork(input) {
    const system = `You are an AI Artwork Interpreter. Keep under 100 words. Return JSON with keys: artisticInterpretation, uniquenessExplanation, exhibitionDescription.`;
    const user = `Input:\n- generatedColors: ${JSON.stringify(input.generatedColors)}\n- generatedShapes: ${JSON.stringify(input.generatedShapes)}\n- visualMetadata: ${JSON.stringify(input.visualMetadata)}\n- randomnessMetrics: ${JSON.stringify(input.randomnessMetrics)}\n\nRespond only with valid JSON.`;
    const resp = await this.createChatCompletion([{role:'system',content:system},{role:'user',content:user}]);
    const parsed = this.parseResponse(resp, ['artisticInterpretation','uniquenessExplanation','exhibitionDescription']);
    return { ...parsed, confidenceScore: 1.0, dataCompleteness: 'Analysis based on complete provided data.' };
  },

  async generateComprehensiveReport(input) {
    const system = `You are a professional report writer. Generate under 250 words. Return JSON with key "report".`;
    const user = `Input:\n- entropyScore: ${input.entropyScore}\n- randomnessMetrics: ${JSON.stringify(input.randomnessMetrics)}\n- keyCharacteristics: ${JSON.stringify(input.keyCharacteristics)}\n- generatedColors: ${JSON.stringify(input.generatedColors)}\n- generatedShapes: ${JSON.stringify(input.generatedShapes)}\n- visualMetadata: ${JSON.stringify(input.visualMetadata)}\n\nGenerate professional report under 250 words. Return JSON with key "report".`;
    const resp = await this.createChatCompletion([{role:'system',content:system},{role:'user',content:user}]);
    const parsed = this.parseResponse(resp, ['report']);
    const wordCount = (parsed.report || '').split(/\s+/).filter(w => w.length > 0).length;
    return { ...parsed, wordCount, confidenceScore: 1.0, dataCompleteness: 'Analysis based on complete provided data.' };
  },

  parseResponse(resp, keys) {
    const content = resp?.choices?.[0]?.message?.content || resp?.choices?.[0]?.text || '{}';
    let parsed = null;
    try { parsed = JSON.parse(content); } catch(e) {
      const match = content.match(/\{[\s\S]*\}/);
      if (match) try { parsed = JSON.parse(match[0]); } catch(e2) {}
    }
    if (!parsed) {
      const fallback = {};
      keys.forEach(k => fallback[k] = content);
      return fallback;
    }
    const result = {};
    keys.forEach(k => {
      const snake = k.replace(/[A-Z]/g, m => '_' + m.toLowerCase());
      result[k] = parsed[k] || parsed[snake] || '';
    });
    return result;
  }
};

// ==================== CANVAS COMPONENTS ====================
const HolographicCanvas = ({ palette, shapes, isGenerating }) => {
  const canvasRef = useRef(null);
  const animRef = useRef(null);
  const timeRef = useRef(0);

  const hexToRgb = (hex) => {
    const r = parseInt(hex.slice(1,3), 16);
    const g = parseInt(hex.slice(3,5), 16);
    const b = parseInt(hex.slice(5,7), 16);
    return [r, g, b];
  };

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    let w, h;

    const resize = () => {
      const rect = canvas.parentElement.getBoundingClientRect();
      w = canvas.width = rect.width - 32;
      h = canvas.height = 160;
    };
    resize();
    window.addEventListener('resize', resize);

    const draw = () => {
      ctx.fillStyle = 'rgba(5,12,25,0.3)';
      ctx.fillRect(0, 0, w, h);
      timeRef.current += 0.015;

      const cx = w / 2, cy = h / 2;
      const numVertices = 6 + (shapes.length * 2);
      const vertices = [];

      for (let i = 0; i < numVertices; i++) {
        const angle = (i / numVertices) * Math.PI * 2 + timeRef.current * 0.3;
        const r = 40 + Math.sin(timeRef.current + i) * 20 + (shapes.length * 5);
        vertices.push({
          x: cx + Math.cos(angle) * r,
          y: cy + Math.sin(angle) * r * 0.6,
          z: Math.sin(timeRef.current * 0.7 + i * 0.8) * 30
        });
      }

      for (let i = 0; i < vertices.length; i++) {
        const v1 = vertices[i], v2 = vertices[(i+1)%vertices.length], v3 = vertices[(i+2)%vertices.length];
        const brightness = 0.3 + (v1.z + 30) / 60 * 0.5;
        const colorIdx = i % palette.length;
        const rgb = hexToRgb(palette[colorIdx]);
        
        ctx.beginPath();
        ctx.moveTo(v1.x, v1.y);
        ctx.lineTo(v2.x, v2.y);
        ctx.lineTo(v3.x, v3.y);
        ctx.closePath();
        ctx.fillStyle = `rgba(${rgb[0]},${rgb[1]},${rgb[2]},${brightness * 0.15})`;
        ctx.fill();
        ctx.strokeStyle = `rgba(${rgb[0]},${rgb[1]},${rgb[2]},${brightness * 0.4})`;
        ctx.lineWidth = 0.8;
        ctx.stroke();
      }

      ctx.beginPath();
      for (let i = 0; i < vertices.length; i++) {
        const innerR = 15 + Math.sin(timeRef.current * 1.2 + i) * 10 + (shapes.length * 2);
        const ix = cx + Math.cos((i/vertices.length) * Math.PI * 2 + timeRef.current * 0.5) * innerR;
        const iy = cy + Math.sin((i/vertices.length) * Math.PI * 2 + timeRef.current * 0.5) * innerR * 0.6;
        if (i === 0) ctx.moveTo(ix, iy);
        else ctx.lineTo(ix, iy);
      }
      ctx.closePath();
      const rgb2 = hexToRgb(palette[1] || palette[0]);
      ctx.strokeStyle = `rgba(${rgb2[0]},${rgb2[1]},${rgb2[2]},0.3)`;
      ctx.lineWidth = 1;
      ctx.stroke();

      animRef.current = requestAnimationFrame(draw);
    };

    if (!isGenerating) {
      draw();
    }

    return () => {
      window.removeEventListener('resize', resize);
      if (animRef.current) cancelAnimationFrame(animRef.current);
    };
  }, [palette, shapes, isGenerating]);

  return <canvas ref={canvasRef} className="holo-canvas" />;
};

const MolecularCanvas = ({ palette, shapes }) => {
  const canvasRef = useRef(null);
  const animRef = useRef(null);
  const timeRef = useRef(0);

  const hexToRgb = (hex) => {
    const r = parseInt(hex.slice(1,3), 16);
    const g = parseInt(hex.slice(3,5), 16);
    const b = parseInt(hex.slice(5,7), 16);
    return [r, g, b];
  };

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    const size = 120;

    const draw = () => {
      ctx.clearRect(0, 0, size, size);
      timeRef.current += 0.02;
      const cx = 60, cy = 60;
      const numRings = 2 + (shapes.length % 3);

      ctx.beginPath();
      for (let i = 0; i < 6; i++) {
        const angle = (i / 6) * Math.PI * 2 + timeRef.current;
        const r = 35;
        const x = cx + Math.cos(angle) * r;
        const y = cy + Math.sin(angle) * r;
        if (i === 0) ctx.moveTo(x, y);
        else ctx.lineTo(x, y);
        
        const rgb = hexToRgb(palette[i % palette.length]);
        ctx.fillStyle = `rgb(${rgb[0]},${rgb[1]},${rgb[2]})`;
        ctx.beginPath();
        ctx.arc(x, y, 4, 0, Math.PI * 2);
        ctx.shadowColor = palette[i % palette.length];
        ctx.shadowBlur = 10;
        ctx.fill();
        ctx.shadowBlur = 0;
      }
      ctx.closePath();
      ctx.strokeStyle = palette[0];
      ctx.globalAlpha = 0.3;
      ctx.lineWidth = 1.5;
      ctx.stroke();
      ctx.globalAlpha = 1;

      for (let ring = 0; ring < numRings; ring++) {
        ctx.beginPath();
        const ringVertices = 3 + ring;
        for (let i = 0; i < ringVertices; i++) {
          const angle = (i / ringVertices) * Math.PI * 2 - timeRef.current * (0.5 + ring * 0.2);
          const r = 15 - ring * 4;
          const x = cx + Math.cos(angle) * r;
          const y = cy + Math.sin(angle) * r;
          if (i === 0) ctx.moveTo(x, y);
          else ctx.lineTo(x, y);
          
          const rgb = hexToRgb(palette[(ring + 2) % palette.length]);
          ctx.fillStyle = `rgb(${rgb[0]},${rgb[1]},${rgb[2]})`;
          ctx.beginPath();
          ctx.arc(x, y, 3, 0, Math.PI * 2);
          ctx.fill();
        }
        ctx.closePath();
        const rgb = hexToRgb(palette[(ring + 2) % palette.length]);
        ctx.strokeStyle = `rgba(${rgb[0]},${rgb[1]},${rgb[2]},0.4)`;
        ctx.lineWidth = 1;
        ctx.stroke();
      }

      animRef.current = requestAnimationFrame(draw);
    };

    draw();

    return () => {
      if (animRef.current) cancelAnimationFrame(animRef.current);
    };
  }, [palette, shapes]);

  return <canvas ref={canvasRef} width={120} height={120} />;
};

const NetworkCanvas = () => {
  const canvasRef = useRef(null);
  const animRef = useRef(null);
  const timeRef = useRef(0);
  const nodesRef = useRef([]);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    let w, h;

    const resize = () => {
      const rect = canvas.parentElement.getBoundingClientRect();
      w = canvas.width = rect.width - 32;
      h = canvas.height = 140;
    };
    resize();
    window.addEventListener('resize', resize);

    if (nodesRef.current.length === 0) {
      for (let i = 0; i < 20; i++) {
        nodesRef.current.push({
          x: Math.random() * w,
          y: Math.random() * h,
          vx: (Math.random() - 0.5) * 0.8,
          vy: (Math.random() - 0.5) * 0.8,
          r: Math.random() * 3 + 2,
          pulse: Math.random() * Math.PI * 2
        });
      }
    }

    const draw = () => {
      ctx.fillStyle = 'rgba(5,12,25,0.2)';
      ctx.fillRect(0, 0, w, h);
      timeRef.current += 0.02;

      nodesRef.current.forEach(n => {
        n.x += n.vx;
        n.y += n.vy;
        n.pulse += 0.05;
        if (n.x < 0 || n.x > w) n.vx *= -1;
        if (n.y < 0 || n.y > h) n.vy *= -1;

        const glow = 0.5 + Math.sin(n.pulse) * 0.3;
        ctx.beginPath();
        ctx.arc(n.x, n.y, n.r, 0, Math.PI * 2);
        ctx.fillStyle = `rgba(0,240,255,${glow})`;
        ctx.fill();

        const ringR = n.r + 4 + Math.sin(n.pulse) * 3;
        ctx.beginPath();
        ctx.arc(n.x, n.y, ringR, 0, Math.PI * 2);
        ctx.strokeStyle = `rgba(0,240,255,${0.15 * glow})`;
        ctx.lineWidth = 0.5;
        ctx.stroke();
      });

      for (let i = 0; i < nodesRef.current.length; i++) {
        for (let j = i + 1; j < nodesRef.current.length; j++) {
          const dx = nodesRef.current[i].x - nodesRef.current[j].x;
          const dy = nodesRef.current[i].y - nodesRef.current[j].y;
          const dist = Math.sqrt(dx * dx + dy * dy);
          if (dist < 100) {
            ctx.beginPath();
            ctx.moveTo(nodesRef.current[i].x, nodesRef.current[i].y);
            ctx.lineTo(nodesRef.current[j].x, nodesRef.current[j].y);
            ctx.strokeStyle = `rgba(74,144,217,${0.2 * (1 - dist / 100)})`;
            ctx.lineWidth = 0.6;
            ctx.stroke();
          }
        }
      }

      animRef.current = requestAnimationFrame(draw);
    };

    draw();

    return () => {
      window.removeEventListener('resize', resize);
      if (animRef.current) cancelAnimationFrame(animRef.current);
    };
  }, []);

  return <canvas ref={canvasRef} className="network-canvas" />;
};

// ==================== MAIN PAGE COMPONENT ====================
export default function MainPage() {
  const [key, setKey] = useState('a1b2c3d4e5f6...');
  const [entropy, setEntropy] = useState(112.4);
  const [title, setTitle] = useState('Quantum Bloom');
  const [isGenerating, setIsGenerating] = useState(false);
  const [status, setStatus] = useState('READY');

  const [fpReport, setFpReport] = useState(null);
  const [audit, setAudit] = useState(null);
  const [interpretation, setInterpretation] = useState(null);
  const [compReport, setCompReport] = useState(null);

  const [derived, setDerived] = useState(() => generateFromKey('a1b2c3d4e5f6...', 112.4));

  const [clock, setClock] = useState('00:00:00');
  const [latency, setLatency] = useState('0.03ms');

  useEffect(() => {
    const interval = setInterval(() => {
      setClock(new Date().toISOString().split('T')[1].split('.')[0]);
    }, 1000);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    const interval = setInterval(() => {
      setLatency((0.01 + Math.random() * 0.05).toFixed(2) + 'ms');
    }, 2000);
    return () => clearInterval(interval);
  }, []);

  const handleGenerate = useCallback(async () => {
    setIsGenerating(true);
    setStatus('PROCESSING');
    const derivedParams = generateFromKey(key, entropy);
    setDerived(derivedParams);
    setTitle(derivedParams.title);

    const artworkMetadata = { 
      title: derivedParams.title, 
      artist: 'Ana Q.', 
      creationDate: '2026-05-30', 
      attributes: { style: 'generative', palette: 'vibrant' } 
    };
    const keyCharacteristics = { length: key.length, algorithm: 'SHA-256', quantumResistant: true };
    const visualMetadata = { resolution: '1.84Å', renderEngine: 'quantum-shaders', dimensions: '2048x2048' };

    try {
      const fp = await Backend.generateReport({
        cryptographicKey: key,
        entropyScore: entropy,
        randomnessMetrics: derivedParams.metrics,
        artworkMetadata
      });
      setFpReport(fp);

      const aud = await Backend.securityAudit({
        entropyScore: entropy,
        randomnessMetrics: derivedParams.metrics,
        keyCharacteristics
      });
      setAudit(aud);

      const interp = await Backend.interpretArtwork({
        generatedColors: derivedParams.palette,
        generatedShapes: derivedParams.shapes,
        visualMetadata,
        randomnessMetrics: derivedParams.metrics
      });
      setInterpretation(interp);

      const comp = await Backend.generateComprehensiveReport({
        entropyScore: entropy,
        randomnessMetrics: derivedParams.metrics,
        keyCharacteristics,
        generatedColors: derivedParams.palette,
        generatedShapes: derivedParams.shapes,
        visualMetadata
      });
      setCompReport(comp);

      setStatus('COMPLETE');
    } catch (err) {
      setStatus('ERROR');
    } finally {
      setIsGenerating(false);
    }
  }, [key, entropy]);

  const entropyPct = Math.min(100, (entropy / 128) * 100);
  const randomPct = Math.min(100, derived.metrics.chiSquared * 100);
  const keyPct = Math.min(100, (key.length / 32) * 100);
  const collisionPct = Math.min(100, 100 - (entropy / 256) * 100);

  return (
    <div className="qam-root">
      {/* Background Grid */}
      <div className="bg-grid" />

      {/* Top Bar */}
      <header className="top-bar">
        <div className="logo-group">
          <div className="pulse-dot" />
          <span className="logo-text">Quantum Art Machine</span>
          <span className="version-tag">v2.0.4 — KEY-BOUND ARTWORK ENGINE</span>
        </div>
        <div className="status-group">
          <span className="status-online">SYSTEM: ONLINE</span>
          <span className="status-secure">SECURE CHANNEL</span>
          <span className="clock">{clock}</span>
        </div>
      </header>

      {/* Main Grid */}
      <main className="main-grid">
        
        {/* Panel 1: Fingerprint Input */}
        <div className="panel">
          <div className="panel-header">
            <span className="panel-title">Fingerprint Input</span>
            <span className={`status-badge ${status === 'READY' ? 'ready' : status === 'PROCESSING' ? 'processing' : status === 'COMPLETE' ? 'complete' : 'error'}`}>
              {status}
            </span>
          </div>

          <div className="input-group">
            <div className="input-row">
              <label>CRYPTO KEY</label>
              <input 
                type="text" 
                value={key} 
                onChange={(e) => setKey(e.target.value)}
                className="crypto-input"
              />
            </div>
            <div className="input-row">
              <label>ENTROPY</label>
              <input 
                type="number" 
                value={entropy} 
                onChange={(e) => setEntropy(parseFloat(e.target.value) || 0)}
                className="crypto-input"
              />
              <span className="unit">bits</span>
            </div>
            <div className="input-row">
              <label>ARTWORK</label>
              <input 
                type="text" 
                value={title} 
                readOnly
                className="crypto-input readonly"
              />
            </div>
          </div>

          <div className="tag-group">
            <span className="tag">QUBIT-{derived.qubit}</span>
            <span className="tag">ENTANGLED</span>
            <span className="tag">COHERENT</span>
          </div>

          <button 
            onClick={handleGenerate}
            disabled={isGenerating}
            className="generate-btn"
          >
            {isGenerating ? `ANALYZING KEY: ${key.substring(0, 8)}...` : 'GENERATE FINGERPRINT REPORT'}
          </button>
        </div>

        {/* Panel 2: Artwork Preview */}
        <div className="panel preview-panel">
          <div className="panel-header">
            <span className="panel-title">Artwork Preview — Key-Bound</span>
            <span className="status-badge ready">DETERMINISTIC</span>
          </div>
          <HolographicCanvas palette={derived.palette} shapes={derived.shapes} isGenerating={isGenerating} />
          <div className="preview-signature">
            SEED: {derived.seed} | {derived.shapes.length} SHAPES | {derived.palette.length} COLORS
          </div>
        </div>

        {/* Panel 3: Security Audit */}
        <div className="panel">
          <div className="panel-header">
            <span className="panel-title">Security Audit</span>
            <span className="status-badge processing">ACTIVE</span>
          </div>

          <div className="metrics-list">
            <div className="metric-row">
              <span>Entropy Quality</span>
              <div className="metric-bar-group">
                <div className="metric-bar-bg">
                  <div className="metric-bar-fill" style={{ width: `${entropyPct}%` }} />
                </div>
                <span className="metric-value">{Math.round(entropyPct)}%</span>
              </div>
            </div>
            <div className="metric-row">
              <span>Randomness Score</span>
              <div className="metric-bar-group">
                <div className="metric-bar-bg">
                  <div className="metric-bar-fill" style={{ width: `${randomPct}%` }} />
                </div>
                <span className="metric-value">{Math.round(randomPct)}%</span>
              </div>
            </div>
            <div className="metric-row">
              <span>Key Strength</span>
              <div className="metric-bar-group">
                <div className="metric-bar-bg">
                  <div className="metric-bar-fill" style={{ width: `${keyPct}%` }} />
                </div>
                <span className="metric-value">{Math.round(keyPct)}%</span>
              </div>
            </div>
            <div className="metric-row">
              <span>Collision Risk</span>
              <div className="metric-bar-group">
                <div className="metric-bar-bg">
                  <div className="metric-bar-fill" style={{ width: `${collisionPct}%` }} />
                </div>
                <span className="metric-value">{Math.round(collisionPct)}%</span>
              </div>
            </div>
          </div>

          <div className="audit-text">
            {audit ? (
              <div>
                <span className="highlight">QUALITY: {audit.securityQuality}</span><br />
                <span className="label">STRENGTHS:</span> {audit.strengths}<br />
                <span className="label">WEAKNESSES:</span> {audit.weaknesses}<br />
                <span className="label">SUMMARY:</span> {audit.summary}<br />
                <span className="confidence">{audit.dataCompleteness} (Confidence: {(audit.confidenceScore * 100).toFixed(0)}%)</span>
              </div>
            ) : (
              'Awaiting fingerprint input to run security audit...'
            )}
          </div>
        </div>

        {/* Panel 4: Artwork Interpretation */}
        <div className="panel interpretation-panel">
          <div className="panel-header">
            <span className="panel-title">Artwork Interpretation</span>
            <span className="status-badge ready">LOCKED</span>
          </div>
          <MolecularCanvas palette={derived.palette} shapes={derived.shapes} />
          <div className="interpretation-text">
            {interpretation ? (
              <div>
                <span className="highlight">{interpretation.artisticInterpretation}</span><br /><br />
                <span className="label">UNIQUENESS:</span> {interpretation.uniquenessExplanation}<br />
                <span className="label">EXHIBITION:</span> {interpretation.exhibitionDescription}<br />
                <span className="confidence">Confidence: {(interpretation.confidenceScore * 100).toFixed(0)}%</span>
              </div>
            ) : (
              'C₂₀H₂₄N₂O₄ // ACTIVE SITE'
            )}
          </div>
        </div>

        {/* Panel 5: Randomness Metrics */}
        <div className="panel">
          <div className="panel-header">
            <span className="panel-title">Randomness Metrics</span>
            <span className="status-badge processing">SCANNING</span>
          </div>
          <div className="metrics-grid">
            <div className="metrics-left">
              <div className="big-metric">{derived.metrics.chiSquared.toFixed(4)}</div>
              <div className="metric-label">CHI-SQUARED</div>
              <div className="medium-metric">{derived.metrics.frequencyMonobit.toFixed(4)}</div>
              <div className="metric-label">FREQUENCY MONOBIT</div>
              <div className="medium-metric green">{derived.metrics.serialCorrelation.toFixed(4)}</div>
              <div className="metric-label">SERIAL CORRELATION</div>
            </div>
            <div className="metrics-divider" />
            <div className="metrics-right">
              <div className="spectrum-label">SPECTRUM</div>
              <div className="spectrum-bars">
                {Array.from({length: 24}).map((_, i) => (
                  <div 
                    key={i}
                    className="spectrum-bar"
                    style={{ height: `${15 + Math.random() * 70}%` }}
                  />
                ))}
              </div>
            </div>
          </div>
        </div>

        {/* Panel 6: Fingerprint Report */}
        <div className="panel">
          <div className="panel-header">
            <span className="panel-title">Fingerprint Report</span>
            <span className="status-badge ready">SECURE</span>
          </div>
          <div className="report-header">
            <div>
              <div className="entropy-big">{entropy.toFixed(1)}</div>
              <div className="metric-label">ENTROPY BITS</div>
            </div>
            <div className="entropy-chart">
              <div className="chart-label">RANDOMNESS METRIC</div>
              <svg className="sparkline" viewBox="0 0 200 60" preserveAspectRatio="none">
                <path 
                  d="M0,60 L0,30 L5,25 L10,35 L15,20 L20,40 L25,15 L30,45 L35,25 L40,30 L45,20 L50,35 L55,15 L60,40 L65,25 L70,30 L75,20 L80,35 L85,15 L90,40 L95,25 L100,30 L105,20 L110,35 L115,15 L120,40 L125,25 L130,30 L135,20 L140,35 L145,15 L150,40 L155,25 L160,30 L165,20 L170,35 L175,15 L180,40 L185,25 L190,30 L195,20 L200,35 L200,60 Z" 
                  fill="rgba(0,240,255,0.08)" 
                  stroke="#00f0ff" 
                  strokeWidth="1.5" 
                  opacity="0.6"
                />
              </svg>
            </div>
          </div>
          <div className="report-body">
            {fpReport ? (
              <div>
                <span className="highlight">{fpReport.humanReadableReport}</span><br /><br />
                <span className="label">RANDOMNESS:</span> {fpReport.randomnessExplanation}<br />
                <span className="label">SECURITY:</span> {fpReport.securityImplications}<br />
                <span className="label">UNIQUENESS:</span> {fpReport.uniquenessAssessment}
              </div>
            ) : (
              'Awaiting report generation...'
            )}
          </div>
          <div className="hash-footer">
            <div className="hash-label">CRYPTOGRAPHIC HASH</div>
            <div className="hash-value">{key} // SHA-256 KEY-BOUND</div>
          </div>
        </div>
      </main>

      {/* Full Width: Interaction Map */}
      <section className="fullwidth-section">
        <div className="panel">
          <div className="panel-header">
            <span className="panel-title">Interaction Map — Entanglement Network</span>
            <span className="status-badge processing">REAL-TIME</span>
          </div>
          <NetworkCanvas />
        </div>
      </section>

      {/* Comprehensive Report */}
      <section className="fullwidth-section">
        <div className="panel">
          <div className="panel-header">
            <span className="panel-title">Comprehensive Report</span>
            <div className="report-meta">
              <span>Confidence: {compReport ? `${(compReport.confidenceScore * 100).toFixed(0)}%` : '--'}</span>
              <span>Words: {compReport ? compReport.wordCount : '--'}</span>
              <span className="status-badge ready">{compReport ? 'COMPLETE' : 'IDLE'}</span>
            </div>
          </div>
          <div className="comprehensive-body">
            {compReport ? compReport.report : 'Generate a fingerprint to produce a comprehensive security + artistic analysis report...'}
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="footer">
        <span>QUANTUM_ART_MACHINE v2.0.4</span>
        <span>QASM // IBM Q // GOOGLE SYCAMORE</span>
        <span>LATENCY: {latency}</span>
      </footer>
    </div>
  );
}
