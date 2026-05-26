import { useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

interface Props {
  rankingTable: string | null;
  onClose: () => void;
}

export default function RankingViewer({ rankingTable, onClose }: Props) {
  const [fontSize, setFontSize] = useState(14);

  if (!rankingTable) return null;

  return (
    <div
      onClick={onClose}
      style={{
        position: "fixed",
        inset: 0,
        backgroundColor: "rgba(0,0,0,0.6)",
        zIndex: 1000,
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
      }}
    >
      {/* Toolbar */}
      <div style={{ position: "absolute", top: 16, right: 16, display: "flex", gap: 8, zIndex: 1001 }}>
        <button
          onClick={(e) => { e.stopPropagation(); setFontSize((s) => Math.min(22, s + 1)); }}
          style={toolBtn}
        >
          A+
        </button>
        <button
          onClick={(e) => { e.stopPropagation(); setFontSize((s) => Math.max(10, s - 1)); }}
          style={toolBtn}
        >
          A-
        </button>
        <button
          onClick={(e) => { e.stopPropagation(); setFontSize(14); }}
          style={toolBtn}
        >
          {fontSize}px
        </button>
        <button onClick={onClose} style={{ ...toolBtn, fontSize: 18 }}>
          ✕
        </button>
      </div>

      {/* Content */}
      <div
        onClick={(e) => e.stopPropagation()}
        style={{
          width: "min(92vw, 900px)",
          maxHeight: "85vh",
          overflow: "auto",
          backgroundColor: "#fff",
          borderRadius: 8,
          padding: "24px 32px",
          fontSize,
          lineHeight: 1.8,
          color: "#333",
        }}
      >
        <h2 style={{ textAlign: "center", marginBottom: 20, color: "#722ed1", fontSize: "1.2em" }}>
          品牌排名分析
        </h2>
        <ReactMarkdown
          remarkPlugins={[remarkGfm]}
          components={{
            table: ({ children }) => (
              <table style={{
                borderCollapse: "collapse", width: "100%", margin: "14px 0",
                fontSize: "0.93em", border: "1px solid #e5e7eb", borderRadius: 8,
              }}>
                {children}
              </table>
            ),
            th: ({ children }) => (
              <th style={{
                border: "1px solid #d1d5db", padding: "10px 14px",
                backgroundColor: "#f5f3ff", fontWeight: 650, textAlign: "left",
                color: "#111827", fontSize: "0.92em",
              }}>
                {children}
              </th>
            ),
            td: ({ children }) => (
              <td style={{
                border: "1px solid #e5e7eb", padding: "9px 14px", color: "#374151",
              }}>
                {children}
              </td>
            ),
            h1: ({ children }) => <h1 style={{ fontSize: "1.3em", fontWeight: 700, margin: "20px 0 12px", color: "#1f2937" }}>{children}</h1>,
            h2: ({ children }) => <h2 style={{ fontSize: "1.15em", fontWeight: 650, margin: "16px 0 10px", color: "#374151" }}>{children}</h2>,
            h3: ({ children }) => <h3 style={{ fontSize: "1.05em", fontWeight: 600, margin: "12px 0 8px", color: "#4b5563" }}>{children}</h3>,
            p: ({ children }) => <p style={{ margin: "0 0 10px 0", lineHeight: 1.7, color: "#374151" }}>{children}</p>,
            strong: ({ children }) => <strong style={{ fontWeight: 700, color: "#111827" }}>{children}</strong>,
            code: ({ children }) => <code style={{ backgroundColor: "#f3f4f6", padding: "2px 6px", borderRadius: 4, fontSize: "0.88em", color: "#e11d48" }}>{children}</code>,
          }}
        >
          {rankingTable}
        </ReactMarkdown>

        <div style={{ textAlign: "center", marginTop: 20, paddingTop: 16, borderTop: "1px solid #f0f0f0" }}>
          <button
            onClick={onClose}
            style={{
              padding: "8px 32px", fontSize: 14, color: "#333",
              backgroundColor: "#f5f5f5", border: "1px solid #d9d9d9",
              borderRadius: 6, cursor: "pointer",
            }}
          >
            返回
          </button>
        </div>
      </div>
    </div>
  );
}

const toolBtn: React.CSSProperties = {
  padding: "6px 14px",
  fontSize: 14,
  backgroundColor: "rgba(255,255,255,0.2)",
  color: "#fff",
  border: "1px solid rgba(255,255,255,0.3)",
  borderRadius: 4,
  cursor: "pointer",
};
