import { useEffect, useRef } from "react";
import * as THREE from "three";

const KEYWORDS = [
  "DeepSeek", "ChatGPT", "Claude", "Gemini", "LLM", "GPT-5",
  "Transformer", "Attention", "RLHF", "Fine-tuning", "RAG",
  "Prompt", "Agent", "多模态", "推理", "蒸馏", "MoE",
  "GEO", "生成式引擎优化", "品牌排名", "搜索意图",
  "品牌提及", "信源", "排名分析", "SEO", "SGE",
  "Answer Engine", "Search Quality", "Brand Authority",
  "Perplexity", "Kimi", "豆包", "文心一言", "通义千问",
  "Copilot", "Grok", "NLP", "Embedding", "Token",
  "Context Window", "Chain-of-Thought", "Zero-shot",
  "Few-shot", "RL", "DL", "Vector DB",
  "华为", "小米", "OPPO", "vivo", "苹果", "三星",
  "特斯拉", "比亚迪", "大疆", "戴森", "索尼",
];

type LetterDef = { char: string; colorTop: string; colorBot: string; glow: string };

const LETTERS: LetterDef[] = [
  { char: "G", colorTop: "#d1d5db", colorBot: "#6b7280", glow: "rgba(156,163,175,0.3)" },
  { char: "E", colorTop: "#bae6fd", colorBot: "#0ea5e9", glow: "rgba(56,189,248,0.35)" },
  { char: "O", colorTop: "#93c5fd", colorBot: "#1d4ed8", glow: "rgba(59,130,246,0.4)" },
];

function sampleLetter(char: string, width: number, height: number, density: number): { x: number; y: number }[] {
  const canvas = document.createElement("canvas");
  canvas.width = width;
  canvas.height = height;
  const ctx = canvas.getContext("2d")!;
  ctx.fillStyle = "#fff";
  ctx.font = `bold ${height * 0.85}px "Arial Black", "Segoe UI Black", sans-serif`;
  ctx.textAlign = "center";
  ctx.textBaseline = "middle";
  ctx.fillText(char, width / 2, height / 2);

  const imageData = ctx.getImageData(0, 0, width, height);
  const points: { x: number; y: number }[] = [];
  const step = Math.max(1, Math.floor(1 / density));
  for (let y = 0; y < height; y += step) {
    for (let x = 0; x < width; x += step) {
      const i = (y * width + x) * 4;
      if (imageData.data[i + 3] > 128) {
        points.push({ x: x - width / 2, y: height / 2 - y });
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

  // Glow effect
  ctx.shadowColor = glow;
  ctx.shadowBlur = 8;
  ctx.font = "bold 22px -apple-system, BlinkMacSystemFont, sans-serif";
  ctx.fillStyle = color;
  ctx.textAlign = "center";
  ctx.textBaseline = "middle";
  ctx.fillText(word, size / 2, size / 8);

  const texture = new THREE.CanvasTexture(canvas);
  texture.minFilter = THREE.LinearFilter;
  const material = new THREE.SpriteMaterial({
    map: texture,
    transparent: true,
    opacity: 0.92,
    depthWrite: false,
  });
  const sprite = new THREE.Sprite(material);
  sprite.scale.set(1.8, 0.45, 1);
  sprite.userData = { word };
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
    const camera = new THREE.PerspectiveCamera(50, width / height, 1, 100);
    camera.position.z = 22;

    const renderer = new THREE.WebGLRenderer({ alpha: true, antialias: true });
    renderer.setSize(width, height);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    container.appendChild(renderer.domElement);

    const group = new THREE.Group();

    // Letter dimensions
    const letterW = 180;
    const letterH = 260;
    const density = 0.5;
    const spacing = letterW * 1.05;
    const totalW = spacing * 3;
    const scale = 0.024;

    let wordIdx = 0;

    LETTERS.forEach((ld, li) => {
      const points = sampleLetter(ld.char, letterW, letterH, density);
      // Thin out + add slight Z variation
      const sampled = points.sort(() => Math.random() - 0.5);

      sampled.forEach((pt) => {
        if (wordIdx >= KEYWORDS.length) return;
        const word = KEYWORDS[wordIdx++ % KEYWORDS.length];

        // Gradient: top to bottom
        const t = (pt.y + letterH / 2) / letterH; // 0(bottom) to 1(top)
        const color = lerpColor(ld.colorTop, ld.colorBot, 1 - t);
        const sprite = createWordSprite(word, color, ld.glow);

        const x = pt.x * scale + (li - 1) * spacing * scale;
        const y = pt.y * scale;
        const z = (Math.random() - 0.5) * 0.6;
        sprite.position.set(x, y, z);
        group.add(sprite);
      });
    });

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
      } else {
        group.rotation.y += 0.003;
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
