import { useEffect, useRef } from "react";
import * as THREE from "three";

const KEYWORDS = [
  // AI / Model
  "DeepSeek", "ChatGPT", "Claude", "Gemini", "LLM", "GPT-5",
  "Transformer", "Attention", "RLHF", "Fine-tuning", "RAG",
  "Prompt", "Agent", "多模态", "推理", "蒸馏", "MoE",
  // GEO / Search
  "GEO", "生成式引擎优化", "品牌排名", "搜索意图",
  "品牌提及", "信源", "排名分析", "SEO", "SGE",
  "Answer Engine", "Search Quality", "Brand Authority",
  // AI Platform
  "Perplexity", "Kimi", "豆包", "文心一言", "通义千问",
  "Copilot", "Bard", "Meta AI", "Grok",
  // Tech Terms
  "NLP", "Embedding", "Token", "Context Window",
  "Chain-of-Thought", "Zero-shot", "Few-shot",
  "RL", "DL", "Vector DB",
  // Brand
  "华为", "小米", "OPPO", "vivo", "苹果", "三星",
  "特斯拉", "比亚迪", "大疆", "戴森", "索尼",
];

function createWordSprite(word: string, color: string): THREE.Sprite {
  const canvas = document.createElement("canvas");
  const size = 256;
  canvas.width = size;
  canvas.height = size / 4;
  const ctx = canvas.getContext("2d")!;

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
    opacity: 0.9,
    depthWrite: false,
  });
  const sprite = new THREE.Sprite(material);
  sprite.scale.set(2.2, 0.55, 1);
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

    // Scene
    const scene = new THREE.Scene();

    // Camera
    const camera = new THREE.PerspectiveCamera(60, width / height, 1, 100);
    camera.position.z = 14;

    // Renderer
    const renderer = new THREE.WebGLRenderer({ alpha: true, antialias: true });
    renderer.setSize(width, height);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    container.appendChild(renderer.domElement);

    // Lights
    const ambient = new THREE.AmbientLight(0xffffff, 0.8);
    scene.add(ambient);

    // Create word sprites on a sphere
    const group = new THREE.Group();
    const radius = 5;
    const colors = [
      "rgba(91,94,247,0.9)",  // primary
      "rgba(139,92,246,0.9)", // purple
      "rgba(16,185,129,0.85)", // green
      "rgba(245,158,11,0.85)", // amber
      "rgba(59,130,246,0.85)", // blue
      "rgba(236,72,153,0.85)", // pink
      "rgba(99,102,241,0.85)", // indigo
      "rgba(148,163,184,0.8)", // slate
    ];

    KEYWORDS.forEach((word, i) => {
      // Fibonacci sphere distribution
      const phi = Math.acos(1 - 2 * (i + 0.5) / KEYWORDS.length);
      const theta = Math.PI * (1 + Math.sqrt(5)) * i;
      const x = radius * Math.sin(phi) * Math.cos(theta);
      const y = radius * Math.sin(phi) * Math.sin(theta);
      const z = radius * Math.cos(phi);

      const color = colors[i % colors.length];
      const sprite = createWordSprite(word, color);
      sprite.position.set(x, y, z);
      group.add(sprite);
    });
    group.position.y = 3;
    scene.add(group);

    // Stars / particles in background
    const starsGeo = new THREE.BufferGeometry();
    const starsCount = 600;
    const starsPos = new Float32Array(starsCount * 3);
    for (let i = 0; i < starsCount; i++) {
      starsPos[i * 3] = (Math.random() - 0.5) * 50;
      starsPos[i * 3 + 1] = (Math.random() - 0.5) * 50;
      starsPos[i * 3 + 2] = (Math.random() - 0.5) * 50;
    }
    starsGeo.setAttribute("position", new THREE.BufferAttribute(starsPos, 3));
    const starsMat = new THREE.PointsMaterial({
      color: 0x8b9cf6,
      size: 0.04,
      transparent: true,
      opacity: 0.7,
      depthWrite: false,
    });
    const stars = new THREE.Points(starsGeo, starsMat);
    scene.add(stars);

    // Mouse interaction: click-drag to rotate + wheel zoom
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
      group.rotation.y += dx * 0.005;
      group.rotation.x += dy * 0.005;
      velocity.y = dx * 0.005;
      velocity.x = dy * 0.005;
      prevMouse = { x: e.clientX, y: e.clientY };
    };

    const onMouseUp = () => { isDragging = false; };

    const onWheel = (e: WheelEvent) => {
      const tag = (e.target as HTMLElement).tagName;
      if (["BUTTON", "INPUT", "A", "SELECT", "TEXTAREA"].includes(tag)) return;
      e.preventDefault();
      camera.position.z += e.deltaY * 0.01;
      camera.position.z = Math.max(5, Math.min(30, camera.position.z));
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

    // Animation loop
    let animId: number;
    const animate = () => {
      animId = requestAnimationFrame(animate);

      // Auto-rotate when idle, drag when pressed
      if (isDragging) {
        // rotation applied during mousemove
      } else if (Math.abs(velocity.x) > 0.0001 || Math.abs(velocity.y) > 0.0001) {
        // Inertia decay after drag release
        group.rotation.y += velocity.y;
        group.rotation.x += velocity.x;
        velocity.x *= 0.95;
        velocity.y *= 0.95;
      } else {
        // Auto random rotation
        group.rotation.y += 0.002;
        group.rotation.x += 0.0005;
      }

      stars.rotation.y += 0.0003;
      stars.rotation.x += 0.0002;

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
      style={{
        position: "fixed",
        inset: 0,
        zIndex: 0,
        pointerEvents: "none",
        background: "radial-gradient(ellipse at center, #1a1a2e 0%, #0f0f1a 60%, #080812 100%)",
      }}
    />
  );
}
