import { useState, type FormEvent } from "react";

interface Props {
  onSubmit: (query: string, brandKeyword: string, platforms: string[]) => Promise<void>;
  disabled?: boolean;
}

const AVAILABLE_PLATFORMS = [
  { key: "deepseek", label: "DeepSeek" },
];

const inputBase: React.CSSProperties = {
  padding: "13px 16px",
  fontSize: 15,
  border: "2px solid var(--color-border)",
  borderRadius: "var(--radius-md)",
  outline: "none",
  transition: "all var(--transition)",
  backgroundColor: "var(--color-surface)",
};

export default function SearchInput({ onSubmit, disabled }: Props) {
  const [query, setQuery] = useState("");
  const [brandKeyword, setBrandKeyword] = useState("");
  const [platforms, setPlatforms] = useState<string[]>(["deepseek"]);
  const [loading, setLoading] = useState(false);
  const [focusQ, setFocusQ] = useState(false);
  const [focusB, setFocusB] = useState(false);

  const togglePlatform = (key: string) => {
    setPlatforms((prev) =>
      prev.includes(key) ? prev.filter((p) => p !== key) : [...prev, key],
    );
  };

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    const trimmed = query.trim();
    if (!trimmed || loading || platforms.length === 0) return;

    setLoading(true);
    try {
      await onSubmit(trimmed, brandKeyword.trim(), platforms);
      setQuery("");
      setBrandKeyword("");
    } finally {
      setLoading(false);
    }
  };

  const disabled_ = disabled || loading || !query.trim() || platforms.length === 0;

  return (
    <form onSubmit={handleSubmit}>
      <div style={{ display: "flex", gap: 12, marginBottom: 12 }}>
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="输入问题，让 Agent 在 DeepSeek 上搜索..."
          disabled={disabled || loading}
          style={{
            ...inputBase,
            flex: 1,
            borderColor: focusQ ? "var(--color-primary)" : "var(--color-border)",
            boxShadow: focusQ ? "0 0 0 3px rgba(91,94,247,0.12)" : "none",
          }}
          onFocus={() => setFocusQ(true)}
          onBlur={() => setFocusQ(false)}
        />
        <input
          type="text"
          value={brandKeyword}
          onChange={(e) => setBrandKeyword(e.target.value)}
          placeholder="品牌关键词（可选）"
          disabled={disabled || loading}
          style={{
            ...inputBase,
            width: 200,
            borderColor: focusB ? "#8b5cf6" : "var(--color-border)",
            boxShadow: focusB ? "0 0 0 3px rgba(139,92,246,0.12)" : "none",
          }}
          onFocus={() => setFocusB(true)}
          onBlur={() => setFocusB(false)}
        />
        <button
          type="submit"
          disabled={disabled_}
          style={{
            padding: "13px 28px",
            fontSize: 15,
            fontWeight: 600,
            color: "#fff",
            border: "none",
            borderRadius: "var(--radius-md)",
            cursor: disabled_ ? "not-allowed" : "pointer",
            transition: "all var(--transition)",
            background: disabled_
              ? "#d1d5db"
              : "var(--color-primary-gradient)",
            opacity: disabled_ ? 0.6 : 1,
            boxShadow: disabled_ ? "none" : "0 4px 14px rgba(91,94,247,0.3)",
          }}
        >
          {loading ? "提交中..." : "搜索"}
        </button>
      </div>

      <div style={{ display: "flex", alignItems: "center", gap: 14, marginBottom: 28 }}>
        <span style={{ fontSize: 13, color: "var(--color-text-muted)", fontWeight: 500 }}>AI 平台</span>
        {AVAILABLE_PLATFORMS.map((p) => (
          <label
            key={p.key}
            style={{
              display: "flex",
              alignItems: "center",
              gap: 6,
              fontSize: 13,
              color: platforms.includes(p.key) ? "var(--color-primary)" : "var(--color-text-muted)",
              cursor: "pointer",
              userSelect: "none",
              fontWeight: platforms.includes(p.key) ? 600 : 400,
              transition: "color var(--transition)",
            }}
          >
            <input
              type="checkbox"
              checked={platforms.includes(p.key)}
              onChange={() => togglePlatform(p.key)}
              style={{ accentColor: "var(--color-primary)", cursor: "pointer", width: 15, height: 15 }}
            />
            {p.label}
          </label>
        ))}
      </div>
    </form>
  );
}
