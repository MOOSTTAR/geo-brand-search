import { useState, type FormEvent } from "react";

interface Platform {
  key: string;
  label: string;
  logo: string;
}

interface Props {
  onSubmit: (query: string, brandKeyword: string, platforms: string[]) => Promise<void>;
  disabled?: boolean;
}

const AVAILABLE_PLATFORMS: Platform[] = [
  { key: "deepseek", label: "DeepSeek", logo: "https://cdn.deepseek.com/site-icons/deepseek.com" },
];

const inputBase: React.CSSProperties = {
  padding: "14px 20px",
  fontSize: 15,
  border: "2px solid var(--color-border)",
  borderRadius: "var(--radius-md)",
  outline: "none",
  transition: "all var(--transition)",
  backgroundColor: "var(--color-surface)",
  width: "100%",
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
    <div style={{
      display: "flex",
      flexDirection: "column",
      alignItems: "center",
      paddingTop: 50,
      animation: "slide-down 0.4s ease",
    }}>
      {/* Hero title */}
      <h2 style={{
        fontSize: 26,
        fontWeight: 700,
        color: "var(--color-text)",
        marginBottom: 8,
        textAlign: "center",
      }}>
        品牌查询
      </h2>
      <p style={{
        fontSize: 14,
        color: "var(--color-text-muted)",
        marginBottom: 36,
        textAlign: "center",
        lineHeight: 1.7,
      }}>
        输入搜索问题，AI 自动分析品牌排名并提取信源
      </p>

      <form onSubmit={handleSubmit} style={{ width: "100%", maxWidth: 560 }}>
        {/* Query input */}
        <div style={{ marginBottom: 12 }}>
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="输入问题，例如：哪个手机好、什么空调性价比高..."
            disabled={disabled || loading}
            style={{
              ...inputBase,
              fontSize: 16,
              padding: "16px 20px",
              borderColor: focusQ ? "var(--color-primary)" : "var(--color-border)",
              boxShadow: focusQ ? "0 0 0 3px rgba(91,94,247,0.12)" : "var(--shadow-sm)",
            }}
            onFocus={() => setFocusQ(true)}
            onBlur={() => setFocusQ(false)}
          />
        </div>

        {/* Brand keyword + button row */}
        <div style={{ display: "flex", gap: 10, marginBottom: 28 }}>
          <input
            type="text"
            value={brandKeyword}
            onChange={(e) => setBrandKeyword(e.target.value)}
            placeholder="品牌关键词（可选，如：华为）"
            disabled={disabled || loading}
            style={{
              ...inputBase,
              flex: 1,
              borderColor: focusB ? "#8b5cf6" : "var(--color-border)",
              boxShadow: focusB ? "0 0 0 3px rgba(139,92,246,0.12)" : "var(--shadow-sm)",
            }}
            onFocus={() => setFocusB(true)}
            onBlur={() => setFocusB(false)}
          />
          <button
            type="submit"
            disabled={disabled_}
            style={{
              padding: "14px 32px",
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
              boxShadow: disabled_ ? "none" : "0 4px 16px rgba(91,94,247,0.35)",
              whiteSpace: "nowrap",
            }}
          >
            {loading ? "提交中..." : "开始搜索"}
          </button>
        </div>

        {/* AI Platform selector */}
        <div style={{ textAlign: "center" }}>
          <span style={{ fontSize: 12, color: "var(--color-text-muted)", fontWeight: 500, marginBottom: 10, display: "block" }}>
            选择 AI 平台
          </span>
          <div style={{ display: "flex", justifyContent: "center", gap: 14 }}>
            {AVAILABLE_PLATFORMS.map((p) => {
              const selected = platforms.includes(p.key);
              return (
                <button
                  key={p.key}
                  type="button"
                  onClick={() => togglePlatform(p.key)}
                  style={{
                    display: "flex",
                    flexDirection: "column",
                    alignItems: "center",
                    gap: 8,
                    padding: "16px 24px",
                    backgroundColor: selected ? "var(--color-primary-light)" : "var(--color-surface)",
                    border: selected ? "2px solid var(--color-primary)" : "2px solid var(--color-border)",
                    borderRadius: "var(--radius-lg)",
                    cursor: "pointer",
                    transition: "all var(--transition)",
                    boxShadow: selected ? "0 0 0 4px rgba(91,94,247,0.08)" : "var(--shadow-sm)",
                  }}
                >
                  <img
                    src={p.logo}
                    alt={p.label}
                    style={{ width: 36, height: 36, borderRadius: 8 }}
                    onError={(e) => {
                      (e.target as HTMLImageElement).style.display = "none";
                    }}
                  />
                  <span style={{
                    fontSize: 12,
                    fontWeight: selected ? 600 : 400,
                    color: selected ? "var(--color-primary)" : "var(--color-text-secondary)",
                  }}>
                    {p.label}
                  </span>
                </button>
              );
            })}
          </div>
        </div>
      </form>
    </div>
  );
}
