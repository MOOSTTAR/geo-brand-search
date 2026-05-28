import { useState, type FormEvent } from "react";

interface Props {
  onSubmit: (query: string, brandKeyword: string, platforms: string[]) => Promise<void>;
  disabled?: boolean;
}

const AVAILABLE_PLATFORMS = [
  { key: "deepseek", label: "DeepSeek" },
];

export default function SearchInput({ onSubmit, disabled }: Props) {
  const [query, setQuery] = useState("");
  const [brandKeyword, setBrandKeyword] = useState("");
  const [platforms, setPlatforms] = useState<string[]>(["deepseek"]);
  const [loading, setLoading] = useState(false);

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

  const inputStyle = {
    padding: "12px 16px",
    fontSize: 15,
    border: "1px solid #d9d9d9",
    borderRadius: 8,
    outline: "none",
    transition: "border-color 0.2s",
  } as const;

  return (
    <form onSubmit={handleSubmit}>
      <div style={{ display: "flex", gap: 12, marginBottom: 12 }}>
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="输入问题，让 Agent 在 DeepSeek 上搜索..."
          disabled={disabled || loading}
          style={{ ...inputStyle, flex: 1 }}
          onFocus={(e) => (e.target.style.borderColor = "#1890ff")}
          onBlur={(e) => (e.target.style.borderColor = "#d9d9d9")}
        />
        <input
          type="text"
          value={brandKeyword}
          onChange={(e) => setBrandKeyword(e.target.value)}
          placeholder="品牌关键词（可选）"
          disabled={disabled || loading}
          style={{ ...inputStyle, width: 200 }}
          onFocus={(e) => (e.target.style.borderColor = "#722ed1")}
          onBlur={(e) => (e.target.style.borderColor = "#d9d9d9")}
        />
        <button
          type="submit"
          disabled={disabled || loading || !query.trim() || platforms.length === 0}
          style={{
            padding: "12px 24px",
            fontSize: 15,
            fontWeight: 500,
            backgroundColor: disabled || loading || !query.trim() || platforms.length === 0 ? "#d9d9d9" : "#1890ff",
            color: "#fff",
            border: "none",
            borderRadius: 8,
            cursor: disabled || loading || !query.trim() || platforms.length === 0 ? "not-allowed" : "pointer",
            transition: "background-color 0.2s",
          }}
        >
          {loading ? "提交中..." : "搜索"}
        </button>
      </div>

      {/* AI 平台选择 */}
      <div style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: 24 }}>
        <span style={{ fontSize: 13, color: "#999" }}>AI 平台:</span>
        {AVAILABLE_PLATFORMS.map((p) => (
          <label
            key={p.key}
            style={{
              display: "flex",
              alignItems: "center",
              gap: 4,
              fontSize: 13,
              color: platforms.includes(p.key) ? "#1890ff" : "#999",
              cursor: "pointer",
              userSelect: "none",
            }}
          >
            <input
              type="checkbox"
              checked={platforms.includes(p.key)}
              onChange={() => togglePlatform(p.key)}
              style={{ cursor: "pointer" }}
            />
            {p.label}
          </label>
        ))}
      </div>
    </form>
  );
}
