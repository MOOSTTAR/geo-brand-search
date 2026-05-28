import { useEffect, useRef } from "react";
import * as THREE from "three";

const KEYWORDS = [
  "DeepSeek", "ChatGPT", "Claude", "Gemini", "GPT-5", "Grok",
  "Kimi", "豆包", "元宝", "文心一言", "通义千问", "百川",
  "Perplexity", "Copilot", "Gemma", "LLaMA", "Qwen", "Mistral",
  "Anthropic", "OpenAI", "Moonshot", "Cohere", "StabilityAI",
  "Midjourney", "Sora", "Suno", "Cursor", "Windsurf", "Bolt",
  "Transformer", "Attention", "RLHF", "Fine-tuning", "RAG",
  "Prompt", "Agent", "多模态", "推理", "蒸馏", "MoE",
  "Token", "Embedding", "VectorDB", "GPU", "TPU", "NPU",
  "LangChain", "LlamaIndex", "CrewAI", "AutoGen", "Dify",
  "GEO", "生成式引擎", "品牌排名", "搜索意图",
  "品牌提及", "信源提取", "排名分析", "SEO", "SGE",
  "AnswerEngine", "BrandAuthority", "搜索优化",
  "华为", "小米", "OPPO", "vivo", "苹果", "三星", "荣耀",
  "一加", "真我", "红米", "魅族", "联想", "摩托罗拉",
  "特斯拉", "比亚迪", "蔚来", "理想", "小鹏", "极氪",
  "大疆", "戴森", "索尼", "Bose", "追觅", "石头",
  "科沃斯", "云鲸", "美的", "格力", "海尔", "海信",
  "TCL", "创维", "方太", "老板", "西门子", "松下",
  "LoRA", "QLoRA", "PEFT", "FlashAttention",
  "AI搜索", "大模型", "语义理解", "知识图谱", "神经网络",
  "AGI", "ASR", "TTS", "CV", "多智能体", "函数调用",
];

type LetterDef = { char: string; colorTop: string; colorBot: string; glow: string };
const LETTERS: LetterDef[] = [
  { char: "G", colorTop: "#e5e7eb", colorBot: "#6b7280", glow: "rgba(156,163,175,0.4)" },
  { char: "E", colorTop: "#e0f2fe", colorBot: "#0ea5e9", glow: "rgba(56,189,248,0.4)" },
  { char: "O", colorTop: "#bfdbfe", colorBot: "#2563eb", glow: "rgba(59,130,246,0.45)" },
];

interface SpriteData { start: THREE.Vector3; end: THREE.Vector3; }

function sampleLetter(char: string, w: number, h: number): { x: number; y: number }[] {
  const canvas = document.createElement("canvas");
  canvas.width = w;
  canvas.height = h;
  const ctx = canvas.getContext("2d")!;
  ctx.fillStyle = "#fff";
  ctx.font = `bold ${h * 0.9}px "Arial Black", "Segoe UI Black", sans-serif`;
  ctx.textAlign = "center";
  ctx.textBaseline = "middle";
  ctx.fillText(char, w / 2, h / 2);
  const imageData = ctx.getImageData(0, 0, w, h);
  const points: { x: number; y: number }[] = [];
  const step = 6;
  for (let y = 0; y < h; y += step) {
    for (let x = 0; x < w; x += step) {
      const i = (y * w + x) * 4;
      if (imageData.data[i + 3] > 100) points.push({ x: x - w / 2, y: h / 2 - y });
    }
  }
  return points;
}

function colorWithVariance(hexA: string, hexB: string, t: number): string {
  const ah = parseInt(hexA.slice(1), 16);
  const bh = parseInt(hexB.slice(1), 16);
  const ar = (ah >> 16) & 0xff, ag = (ah >> 8) & 0xff, ab = ah & 0xff;
  const br = (bh >> 16) & 0xff, bg = (bh >> 8) & 0xff, bb = bh & 0xff;
  const baseR = ar + (br - ar) * t, baseG = ag + (bg - ag) * t, baseB = ab + (bb - ab) * t;
  const v = 18;
  const R = Math.round(clamp(baseR + (Math.random() - 0.5) * v * 2, 0, 255));
  const G = Math.round(clamp(baseG + (Math.random() - 0.5) * v * 2, 0, 255));
  const B = Math.round(clamp(baseB + (Math.random() - 0.5) * v * 2, 0, 255));
  return `rgb(${R},${G},${B})`;
}
function clamp(v: number, min: number, max: number) { return Math.max(min, Math.min(max, v)); }

function easeOutCubic(t: number) { return 1 - Math.pow(1 - t, 3); }

function createWordSprite(word: string, color: string, glow: string): THREE.Sprite {
  const canvas = document.createElement("canvas");
  const size = 128;
  canvas.width = size;
  canvas.height = size / 4;
  const ctx = canvas.getContext("2d")!;
  ctx.shadowColor = glow;
  ctx.shadowBlur = 6;
  ctx.font = "bold 16px -apple-system, BlinkMacSystemFont, sans-serif";
  ctx.fillStyle = color;
  ctx.textAlign = "center";
  ctx.textBaseline = "middle";
  ctx.fillText(word, size / 2, size / 8);
  const texture = new THREE.CanvasTexture(canvas);
  texture.minFilter = THREE.LinearFilter;
  const material = new THREE.SpriteMaterial({ map: texture, transparent: true, opacity: 0.9, depthWrite: false });
  const sprite = new THREE.Sprite(material);
  sprite.scale.set(1.4, 0.35, 1);
  return sprite;
}

interface Props {
  visible: boolean;
  intro: boolean;
  scrollProgress: number;
  scaleProgress: number;
  onIntroDone?: () => void;
}

export default function TechBackground({ visible, intro, scrollProgress, scaleProgress, onIntroDone }: Props) {
  const containerRef = useRef<HTMLDivElement>(null);
  const visibleRef = useRef(visible);
  visibleRef.current = visible;
  const scrollRef = useRef(scrollProgress);
  scrollRef.current = scrollProgress;
  const scaleRef = useRef(scaleProgress);
  scaleRef.current = scaleProgress;

  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    const width = window.innerWidth;
    const height = window.innerHeight;

    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(45, width / height, 1, 100);
    camera.position.z = 24;
    const renderer = new THREE.WebGLRenderer({ alpha: true, antialias: true });
    renderer.setSize(width, height);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    const canvas = renderer.domElement;
    canvas.style.cursor = "grab";
    canvas.style.pointerEvents = "auto";
    container.appendChild(canvas);

    const group = new THREE.Group();
    const sprites: { s: THREE.Sprite; d: SpriteData }[] = [];
    scene.add(group);

    // Precompute target points for GEO letters
    const letterW = 200, letterH = 300, spacing = 240, scale = 0.03;
    const shuffled = [...KEYWORDS].sort(() => Math.random() - 0.5);
    const spreadRadius = 20;
    const allTargets: { pt: { x: number; y: number }; ld: LetterDef | null; word: string; ez?: number }[] = [];

    LETTERS.forEach((ld, li) => {
      const pts = sampleLetter(ld.char, letterW, letterH);
      const target2 = 220;
      const thinRate = Math.max(1, Math.floor(pts.length / target2));
      const thinned = pts.filter((_, i) => i % thinRate === 0);
      const words = [...shuffled].sort(() => Math.random() - 0.5);
      thinned.forEach((pt, pi) => {
        allTargets.push({ pt, ld, word: words[pi % words.length] });
      });
    });

    // Shell particles: hollow sphere wall around GEO
    const shellColors = ["#e5e7eb", "#bae6fd", "#93c5fd", "#7dd3fc", "#cbd5e1", "#94a3b8"];
    const shellCount = 300;
    const shellInner = 14, shellOuter = 18;
    const shellWords = [...shuffled].sort(() => Math.random() - 0.5);
    for (let i = 0; i < shellCount; i++) {
      const r = shellInner + Math.random() * (shellOuter - shellInner);
      const theta = Math.random() * Math.PI * 2;
      const phi = Math.acos(2 * Math.random() - 1);
      const ex = Math.sin(phi) * Math.cos(theta) * r;
      const ey = Math.sin(phi) * Math.sin(theta) * r;
      const ez = Math.cos(phi) * r;
      allTargets.push({
        pt: { x: ex / scale, y: ey / scale },
        ld: null,
        word: shellWords[i % shellWords.length],
        ez: Math.cos(phi) * r,
      });
    }

    // Create sprites in chunks — allow paint between batches
    let introStart = 0;
    const totalItems = allTargets.length;
    const CHUNK = 120;
    let idx = 0;

    function createChunk() {
      const end = Math.min(idx + CHUNK, totalItems);
      for (let i = idx; i < end; i++) {
        const { pt, ld, word } = allTargets[i];
        let color: string, glow: string;
        if (ld) {
          const t = (pt.y + letterH / 2) / letterH;
          color = colorWithVariance(ld.colorTop, ld.colorBot, 1 - t);
          glow = ld.glow;
        } else {
          const sc = shellColors[Math.floor(Math.random() * shellColors.length)];
          color = colorWithVariance(sc, sc, Math.random());
          glow = "rgba(148,163,184,0.2)";
        }
        const sprite = createWordSprite(word, color, glow);
        let ex: number, ey: number;
        if (ld) {
          const li = LETTERS.indexOf(ld);
          ex = pt.x * scale + (li - 1) * spacing * scale;
          ey = pt.y * scale;
        } else {
          ex = pt.x * scale;
          ey = pt.y * scale;
        }
        const ez = allTargets[i].ez ?? (Math.random() - 0.5) * 1.5;
        const theta2 = Math.random() * Math.PI * 2;
        const phi2 = Math.acos(2 * Math.random() - 1);
        const sx = Math.sin(phi2) * Math.cos(theta2) * spreadRadius;
        const sy = Math.sin(phi2) * Math.sin(theta2) * spreadRadius;
        const sz = Math.cos(phi2) * spreadRadius;
        const data: SpriteData = {
          start: new THREE.Vector3(sx, sy, sz),
          end: new THREE.Vector3(ex, ey, ez),
        };
        sprite.position.copy(data.start);
        sprites.push({ s: sprite, d: data });
        group.add(sprite);
      }
      idx = end;
      renderer.render(scene, camera);
      if (idx < totalItems) {
        setTimeout(createChunk, 0);
      } else {
        introStart = performance.now();
      }
    }
    createChunk();

    const INTRO_DURATION = 2800;
    let introDone = false;

    // Mouse interaction
    let isDragging = false;
    let prevMouse = { x: 0, y: 0 };
    let velocity = { x: 0, y: 0 };

    const onMouseDown = (e: MouseEvent) => {
      if (intro && !introDone) return;
      const tag = (e.target as HTMLElement).tagName;
      if (["BUTTON", "INPUT", "A", "SELECT", "TEXTAREA"].includes(tag)) return;
      if ((e.target as HTMLElement).closest("button, input, a, select, textarea")) return;
      isDragging = true;
      velocity.x = 0; velocity.y = 0;
      prevMouse = { x: e.clientX, y: e.clientY };
      canvas.style.cursor = "grabbing";
    };

    const onMouseMove = (e: MouseEvent) => {
      if (!isDragging) return;
      const dx = e.clientX - prevMouse.x, dy = e.clientY - prevMouse.y;
      group.rotation.y += dx * 0.003;
      group.rotation.x += dy * 0.003;
      velocity.y = dx * 0.003; velocity.x = dy * 0.003;
      prevMouse = { x: e.clientX, y: e.clientY };
    };

    const onMouseUp = () => {
      isDragging = false;
      canvas.style.cursor = "grab";
      group.rotation.x = ((group.rotation.x + Math.PI) % (Math.PI * 2)) - Math.PI;
      group.rotation.y = ((group.rotation.y + Math.PI) % (Math.PI * 2)) - Math.PI;
    };

    const onResize = () => {
      const w = window.innerWidth, h = window.innerHeight;
      camera.aspect = w / h;
      camera.updateProjectionMatrix();
      renderer.setSize(w, h);
    };

    window.addEventListener("mousedown", onMouseDown);
    window.addEventListener("mousemove", onMouseMove);
    window.addEventListener("mouseup", onMouseUp);
    window.addEventListener("resize", onResize);

    let animId: number;
    const animate = () => {
      animId = requestAnimationFrame(animate);
      if (!visibleRef.current) return;

      if (introStart > 0) {
        const elapsed = performance.now() - introStart;
        const t = Math.min(elapsed / INTRO_DURATION, 1);
        const eased = easeOutCubic(t);

        sprites.forEach(({ s, d }) => {
          s.position.lerpVectors(d.start, d.end, eased);
        });

        if (t >= 1 && !introDone) {
          introDone = true;
          onIntroDone?.();
        }
      }

      // Scroll-driven: position, scale, tilt
      const sp = scrollRef.current;
      const sc = scaleRef.current;
      group.position.y = sp * 6;
      group.scale.setScalar(1 - sc * 0.25);
      const tiltX = sp * 0.27;

      // Rotation logic (only after intro)
      if (introDone) {
        if (isDragging) {
          // during mousemove
        } else if (Math.abs(velocity.x) > 0.0001 || Math.abs(velocity.y) > 0.0001) {
          group.rotation.y += velocity.y;
          group.rotation.x += velocity.x;
          velocity.x *= 0.95;
          velocity.y *= 0.95;
        } else {
          group.rotation.x += (tiltX - group.rotation.x) * 0.04;
          group.rotation.y += (0 - group.rotation.y) * 0.04;
        }
      }

      renderer.render(scene, camera);
    };
    animate();

    return () => {
      cancelAnimationFrame(animId);
      window.removeEventListener("mousemove", onMouseMove);
      window.removeEventListener("mousedown", onMouseDown);
      window.removeEventListener("mouseup", onMouseUp);
      window.removeEventListener("resize", onResize);
      renderer.dispose();
      container.removeChild(canvas);
    };
  }, []);

  return (
    <div
      ref={containerRef}
      style={{
        position: "fixed",
        inset: 0,
        zIndex: 0,
        display: visible ? "block" : "none",
        background: intro
          ? `radial-gradient(ellipse at center, rgba(30,30,48,${1 - scrollProgress}) 0%, rgba(13,13,20,${1 - scrollProgress}) 100%)`
          : "linear-gradient(to bottom, rgba(13,13,20,0.6) 0%, rgba(13,13,20,0.2) 40%, transparent 70%)",
      }}
    />
  );
}
