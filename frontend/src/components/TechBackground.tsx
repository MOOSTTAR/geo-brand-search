import { useEffect, useRef } from "react";
import * as THREE from "three";

const KEYWORDS = [
  // AI models & platforms
  "DeepSeek", "ChatGPT", "Claude", "Gemini", "GPT-5", "Grok",
  "Kimi", "豆包", "元宝", "文心一言", "通义千问", "百川",
  "Perplexity", "Copilot", "Gemma", "LLaMA", "Qwen", "Mistral",
  "CommandR", "Cohere", "Anthropic", "OpenAI", "Moonshot",
  // Core tech
  "Transformer", "Attention", "RLHF", "Fine-tuning", "RAG",
  "Prompt", "Agent", "多模态", "推理", "蒸馏", "MoE",
  "Token", "Embedding", "VectorDB", "GPU", "TPU", "NPU",
  "LangChain", "LlamaIndex", "CrewAI", "AutoGen",
  // GEO / Search
  "GEO", "GenerativeEngine", "品牌排名", "搜索意图",
  "品牌提及", "信源提取", "排名分析", "SEO", "SGE",
  "AnswerEngine", "SearchQuality", "BrandAuthority",
  "生成式引擎", "搜索优化", "位置追踪",
  // Brands
  "华为", "小米", "OPPO", "vivo", "苹果", "三星", "荣耀",
  "一加", "真我", "红米", "魅族", "联想", "摩托罗拉",
  "特斯拉", "比亚迪", "蔚来", "理想", "小鹏", "极氪",
  "大疆", "戴森", "索尼", "Bose", "追觅", "石头",
  "科沃斯", "云鲸", "美的", "格力", "海尔", "海信",
  "TCL", "创维", "方太", "老板", "西门子", "松下",
  // More terms
  "ContextWindow", "ChainOfThought", "ZeroShot",
  "FewShot", "RL", "DL", "NLP", "CV", "ASR", "TTS",
  "LoRA", "QLoRA", "PEFT", "FlashAttention",
  "AI搜索", "大模型", "语义理解", "知识图谱",
];

type LetterDef = { char: string; colorTop: string; colorBot: string; glow: string };

const LETTERS: LetterDef[] = [
  { char: "G", colorTop: "#e5e7eb", colorBot: "#6b7280", glow: "rgba(156,163,175,0.4)" },
  { char: "E", colorTop: "#e0f2fe", colorBot: "#0ea5e9", glow: "rgba(56,189,248,0.4)" },
  { char: "O", colorTop: "#bfdbfe", colorBot: "#2563eb", glow: "rgba(59,130,246,0.45)" },
];

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
  const step = 3; // sample every 3 pixels
  for (let y = 0; y < h; y += step) {
    for (let x = 0; x < w; x += step) {
      const i = (y * w + x) * 4;
      if (imageData.data[i + 3] > 100) {
        points.push({ x: x - w / 2, y: h / 2 - y });
      }
    }
  }
  return points;
}

function lerpColor(hexA: string, hexB: string, t: number): string {
  const ah = parseInt(hexA.slice(1), 16);
  const bh = parseInt(hexB.slice(1), 16);
  const ar = (ah >> 16) & 0xff, ag = (ah >> 8) & 0xff, ab = ah & 0xff;
  const br = (bh >> 16) & 0xff, bg = (bh >> 8) & 0xff, bb = bh & 0xff;
  const R = Math.round(ar + (br - ar) * t);
  const G = Math.round(ag + (bg - ag) * t);
  const B = Math.round(ab + (bb - ab) * t);
  return `rgb(${R},${G},${B})`;
}

function createWordSprite(word: string, color: string, glow: string): THREE.Sprite {
  const canvas = document.createElement("canvas");
  const size = 256;
  canvas.width = size;
  canvas.height = size / 4;
  const ctx = canvas.getContext("2d")!;

  ctx.shadowColor = glow;
  ctx.shadowBlur = 10;
  ctx.font = "bold 18px -apple-system, BlinkMacSystemFont, sans-serif";
  ctx.fillStyle = color;
  ctx.textAlign = "center";
  ctx.textBaseline = "middle";
  ctx.fillText(word, size / 2, size / 8);

  const texture = new THREE.CanvasTexture(canvas);
  texture.minFilter = THREE.LinearFilter;
  const material = new THREE.SpriteMaterial({
    map: texture,
    transparent: true,
    opacity: 0.9,
    depthWrite: false,
  });
  const sprite = new THREE.Sprite(material);
  sprite.scale.set(1.5, 0.38, 1);
  return sprite;
}

export default function TechBackground() {
  const containerRef = useRef<HTMLDivElement>(null);

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
    container.appendChild(renderer.domElement);

    const group = new THREE.Group();

    // Bigger letter canvas for more detail
    const letterW = 280;
    const letterH = 400;
    const spacing = 330;
    const scale = 0.025;

    let wordIdx = 0;

    LETTERS.forEach((ld, li) => {
      const pts = sampleLetter(ld.char, letterW, letterH);

      pts.forEach((pt) => {
        if (wordIdx >= KEYWORDS.length) wordIdx = 0;
        const word = KEYWORDS[wordIdx++];

        const t = (pt.y + letterH / 2) / letterH;
        const color = lerpColor(ld.colorTop, ld.colorBot, 1 - t);
        const sprite = createWordSprite(word, color, ld.glow);

        const x = pt.x * scale + (li - 1) * spacing * scale;
        const y = pt.y * scale;
        const z = (Math.random() - 0.5) * 0.5;
        sprite.position.set(x, y, z);
        group.add(sprite);
      });
    });

    group.position.y = 5;
    scene.add(group);

    // Mouse interaction
    let isDragging = false;
    let prevMouse = { x: 0, y: 0 };
    let velocity = { x: 0, y: 0 };

    const onMouseDown = (e: MouseEvent) => {
      const tag = (e.target as HTMLElement).tagName;
      if (["BUTTON", "INPUT", "A", "SELECT", "TEXTAREA"].includes(tag)) return;
      if ((e.target as HTMLElement).closest("button, input, a, select, textarea")) return;
      isDragging = true;
      velocity.x = 0;
      velocity.y = 0;
      prevMouse = { x: e.clientX, y: e.clientY };
    };

    const onMouseMove = (e: MouseEvent) => {
      if (!isDragging) return;
      const dx = e.clientX - prevMouse.x;
      const dy = e.clientY - prevMouse.y;
      group.rotation.y += dx * 0.003;
      group.rotation.x += dy * 0.003;
      velocity.y = dx * 0.003;
      velocity.x = dy * 0.003;
      prevMouse = { x: e.clientX, y: e.clientY };
    };

    const onMouseUp = () => { isDragging = false; };

    const onWheel = (e: WheelEvent) => {
      const tag = (e.target as HTMLElement).tagName;
      if (["BUTTON", "INPUT", "A", "SELECT", "TEXTAREA"].includes(tag)) return;
      e.preventDefault();
      camera.position.z += e.deltaY * 0.01;
      camera.position.z = Math.max(10, Math.min(40, camera.position.z));
    };

    const onResize = () => {
      const w = window.innerWidth;
      const h = window.innerHeight;
      camera.aspect = w / h;
      camera.updateProjectionMatrix();
      renderer.setSize(w, h);
    };

    window.addEventListener("mousedown", onMouseDown);
    window.addEventListener("mousemove", onMouseMove);
    window.addEventListener("mouseup", onMouseUp);
    window.addEventListener("wheel", onWheel, { passive: false });
    window.addEventListener("resize", onResize);

    let animId: number;
    const animate = () => {
      animId = requestAnimationFrame(animate);

      if (isDragging) {
        // rotation during mousemove
      } else if (Math.abs(velocity.x) > 0.0001 || Math.abs(velocity.y) > 0.0001) {
        group.rotation.y += velocity.y;
        group.rotation.x += velocity.x;
        velocity.x *= 0.95;
        velocity.y *= 0.95;
      }

      renderer.render(scene, camera);
    };
    animate();

    return () => {
      cancelAnimationFrame(animId);
      window.removeEventListener("mousemove", onMouseMove);
      window.removeEventListener("mousedown", onMouseDown);
      window.removeEventListener("mouseup", onMouseUp);
      window.removeEventListener("wheel", onWheel);
      window.removeEventListener("resize", onResize);
      renderer.dispose();
      container.removeChild(renderer.domElement);
    };
  }, []);

  return (
    <div
      ref={containerRef}
      style={{ position: "fixed", inset: 0, zIndex: 0, pointerEvents: "none" }}
    />
  );
}
