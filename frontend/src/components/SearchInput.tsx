import { useState, type FormEvent } from "react";

interface Props {
  onSubmit: (query: string, brandKeyword: string) => Promise<void>;
  disabled?: boolean;
}

export default function SearchInput({ onSubmit, disabled }: Props) {
  const [query, setQuery] = useState("");
  const [brandKeyword, setBrandKeyword] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    const trimmed = query.trim();
    if (!trimmed || loading) return;

    setLoading(true);
    try {
      await onSubmit(trimmed, brandKeyword.trim());
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
    <form onSubmit={handleSubmit} style={{ display: "flex", gap: 12, marginBottom: 24 }}>
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
        disabled={disabled || loading || !query.trim()}
        style={{
          padding: "12px 24px",
          fontSize: 15,
          fontWeight: 500,
          backgroundColor: disabled || loading || !query.trim() ? "#d9d9d9" : "#1890ff",
          color: "#fff",
          border: "none",
          borderRadius: 8,
          cursor: disabled || loading || !query.trim() ? "not-allowed" : "pointer",
          transition: "background-color 0.2s",
        }}
      >
        {loading ? "提交中..." : "搜索"}
      </button>
    </form>
  );
}
