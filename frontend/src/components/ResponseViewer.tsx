import { useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

interface Props {
  text: string | null;
  thinkingText: string | null;
  answerText: string | null;
  answerHtml: string | null;
  onClose: () => void;
}

const MARKDOWN_PLUGINS = [remarkGfm];

/** DeepSeek-style dark code block with language label and copy button */
function CodeBlock({ language, children }: { language: string; children: string }) {
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    navigator.clipboard.writeText(children).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    });
  };

  return (
    <div style={codeBlockWrapper}>
      <div style={codeBlockBanner}>
        <span style={codeLangLabel}>{language || "code"}</span>
        <button onClick={handleCopy} style={copyBtn}>
          {copied ? "已复制" : "复制"}
        </button>
      </div>
      <pre style={codePre}>
        <code>{children}</code>
      </pre>
    </div>
  );
}

export default function ResponseViewer({ text, thinkingText, answerText, answerHtml, onClose }: Props) {
  const [fontSize, setFontSize] = useState(14);
  const [showThinking, setShowThinking] = useState(false);

  // Use separate DOM-extracted fields if available, otherwise fall back to text
  const thinking = thinkingText || "";
  const answer = answerText || text || "";
  const html = answerHtml || null;

  if (!text && !answer) return null;

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
      <div
        style={{
          position: "absolute",
          top: 16,
          right: 16,
          display: "flex",
          gap: 8,
          zIndex: 1001,
        }}
      >
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
          width: "min(90vw, 800px)",
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
        {/* Thinking process — collapsible */}
        {thinking && (
          <div style={{ marginBottom: 16 }}>
            <button
              onClick={() => setShowThinking(!showThinking)}
              style={{
                display: "flex",
                alignItems: "center",
                gap: 6,
                padding: "8px 14px",
                fontSize: 13,
                color: "#8c8c8c",
                backgroundColor: "#fafafa",
                border: "1px solid #f0f0f0",
                borderRadius: 6,
                cursor: "pointer",
                width: "100%",
                textAlign: "left",
              }}
            >
              <span style={{ fontSize: 16, lineHeight: 1 }}>
                {showThinking ? "▾" : "▸"}
              </span>
              <span>思考过程 ({thinking.length} 字)</span>
              <span style={{
                marginLeft: 8,
                fontSize: 11,
                padding: "1px 8px",
                borderRadius: 3,
                backgroundColor: "#fff1f0",
                color: "#cf1322",
                border: "1px solid #ffa39e",
              }}>
                思考
              </span>
            </button>
            {showThinking && (
              <div
                style={{
                  marginTop: 8,
                  padding: "12px 16px",
                  backgroundColor: "#fafafa",
                  borderRadius: 6,
                  border: "1px solid #f0f0f0",
                  fontSize: Math.max(12, fontSize - 1),
                  color: "#8c8c8c",
                  whiteSpace: "pre-wrap",
                  lineHeight: 1.7,
                  maxHeight: 300,
                  overflow: "auto",
                }}
              >
                {thinking}
              </div>
            )}
          </div>
        )}

        {/* Divider between thinking and answer */}
        {thinking && (
          <div style={{
            display: "flex",
            alignItems: "center",
            gap: 12,
            margin: "8px 0 20px",
          }}>
            <div style={{ flex: 1, height: 1, backgroundColor: "#e8e8e8" }} />
            <span style={{
              fontSize: 12,
              color: "#8c8c8c",
              whiteSpace: "nowrap",
              padding: "2px 10px",
              backgroundColor: "#f6ffed",
              border: "1px solid #b7eb8f",
              borderRadius: 3,
            }}>
              回复内容
            </span>
            <div style={{ flex: 1, height: 1, backgroundColor: "#e8e8e8" }} />
          </div>
        )}

        {/* Main answer — HTML from DeepSeek, or markdown fallback */}
        {html ? (
          <div className="ds-answer-html" style={{ fontFamily: mdFont }}>
            <style>{`
              .ds-answer-html p,
              .ds-answer-html .ds-markdown-paragraph {
                margin: 0 0 14px 0;
                line-height: 1.85;
                color: #374151;
              }
              .ds-answer-html strong {
                font-weight: 700;
                color: #111827;
              }
              .ds-answer-html code {
                background-color: #f3f4f6;
                padding: 2px 7px;
                border-radius: 4px;
                font-size: 0.88em;
                font-family: "SF Mono", "Fira Code", Consolas, Monaco, monospace;
                color: #e11d48;
                border: 1px solid #e5e7eb;
              }
              .ds-answer-html pre {
                margin: 0;
                padding: 14px 16px;
                overflow: auto;
                font-size: 0.84em;
                line-height: 1.65;
                color: #334155;
                font-family: "SF Mono", "Fira Code", Consolas, Monaco, monospace;
                background-color: transparent;
              }
              .ds-answer-html .md-code-block {
                margin: 14px 0;
                border-radius: 10px;
                overflow: hidden;
                background-color: #f8fafc;
                border: 1px solid #e2e8f0;
              }
              .ds-answer-html .md-code-block-light {
                background-color: #f8fafc;
              }
              .ds-answer-html .token.tag { color: #22863a; }
              .ds-answer-html .token.punctuation { color: #6a737d; }
              .ds-answer-html .token.attr-name { color: #6f42c1; }
              .ds-answer-html .token.attr-value { color: #032f62; }
              .ds-answer-html .token.string { color: #032f62; }
              .ds-answer-html .token.comment { color: #6a737d; font-style: italic; }
              .ds-answer-html .token.keyword { color: #d73a49; }
              .ds-answer-html .token.function { color: #6f42c1; }
              .ds-answer-html .token.number { color: #005cc5; }
              .ds-answer-html .token.operator { color: #d73a49; }
              .ds-answer-html ul, .ds-answer-html ol {
                padding-left: 22px;
                margin: 8px 0 14px;
                line-height: 1.8;
                color: #374151;
              }
              .ds-answer-html li { margin-bottom: 6px; line-height: 1.75; }
              .ds-answer-html li p { margin: 0 0 4px 0; }
              .ds-answer-html table {
                border-collapse: collapse;
                width: 100%;
                margin: 14px 0;
                font-size: 0.93em;
                border: 1px solid #e5e7eb;
              }
              .ds-answer-html th {
                border: 1px solid #d1d5db;
                padding: 10px 14px;
                background-color: #f9fafb;
                font-weight: 650;
                text-align: left;
                color: #111827;
              }
              .ds-answer-html td {
                border: 1px solid #e5e7eb;
                padding: 9px 14px;
                color: #374151;
              }
              .ds-answer-html h1 {
                font-size: 1.5em; font-weight: 700;
                margin: 28px 0 16px; padding-bottom: 10px;
                border-bottom: 2px solid #e5e7eb; color: #111827;
              }
              .ds-answer-html h2 {
                font-size: 1.3em; font-weight: 700;
                margin: 24px 0 12px; color: #1f2937;
              }
              .ds-answer-html h3 {
                font-size: 1.15em; font-weight: 650;
                margin: 20px 0 10px; color: #374151;
              }
              .ds-answer-html h4 {
                font-size: 1.05em; font-weight: 600;
                margin: 16px 0 8px; color: #4b5563;
              }
              .ds-answer-html blockquote {
                border-left: 4px solid #6366f1; padding: 10px 18px;
                margin: 14px 0; color: #4b5563;
                background-color: #f8fafc; border-radius: 0 6px 6px 0;
              }
              .ds-answer-html a {
                color: #2563eb; text-decoration: none;
                border-bottom: 1px solid rgba(37,99,235,0.3);
              }
              .ds-answer-html hr {
                border: none; border-top: 1px solid #e5e7eb; margin: 24px 0;
              }
              .ds-answer-html em { font-style: italic; }
            `}</style>
            <div dangerouslySetInnerHTML={{ __html: html }} />
          </div>
        ) : (
          <ReactMarkdown
            remarkPlugins={MARKDOWN_PLUGINS}
            components={{
              h1: ({ children, ...props }) => (
                <h1 style={h1Style} {...props}>{children}</h1>
              ),
              h2: ({ children, ...props }) => (
                <h2 style={h2Style} {...props}>{children}</h2>
              ),
              h3: ({ children, ...props }) => (
                <h3 style={h3Style} {...props}>{children}</h3>
              ),
              h4: ({ children, ...props }) => (
                <h4 style={h4Style} {...props}>{children}</h4>
              ),
              p: ({ children, ...props }) => (
                <p style={pStyle} {...props}>{children}</p>
              ),
              ul: ({ children, ...props }) => (
                <ul style={ulStyle} {...props}>{children}</ul>
              ),
              ol: ({ children, ...props }) => (
                <ol style={olStyle} {...props}>{children}</ol>
              ),
              li: ({ children, ...props }) => (
                <li style={liStyle} {...props}>{children}</li>
              ),
              code: ({ className, children, ...props }: any) => {
                const isInline = !className;
                if (isInline) {
                  return <code style={inlineCodeStyle} {...props}>{children}</code>;
                }
                const lang = className ? className.replace("language-", "") : "";
                return <CodeBlock language={lang}>{String(children).replace(/\n$/, "")}</CodeBlock>;
              },
              blockquote: ({ children, ...props }) => (
                <blockquote style={blockquoteStyle} {...props}>{children}</blockquote>
              ),
              table: ({ children, ...props }) => (
                <div style={{ overflowX: "auto", margin: "14px 0" }}>
                  <table style={tableStyle} {...props}>{children}</table>
                </div>
              ),
              th: ({ children, ...props }) => (
                <th style={thStyle} {...props}>{children}</th>
              ),
              td: ({ children, ...props }) => (
                <td style={tdStyle} {...props}>{children}</td>
              ),
              hr: (props) => <hr style={hrStyle} {...props} />,
              strong: ({ children, ...props }) => (
                <strong style={strongStyle} {...props}>{children}</strong>
              ),
              a: ({ children, href, ...props }) => (
                <a href={href} target="_blank" rel="noopener noreferrer" style={linkStyle} {...props}>{children}</a>
              ),
            }}
          >
            {answer}
          </ReactMarkdown>
        )}

        {/* 返回按钮 */}
        <div style={{ textAlign: "center", marginTop: 20, paddingTop: 16, borderTop: "1px solid #f0f0f0" }}>
          <button
            onClick={onClose}
            style={{
              padding: "8px 32px",
              fontSize: 14,
              color: "#333",
              backgroundColor: "#f5f5f5",
              border: "1px solid #d9d9d9",
              borderRadius: 6,
              cursor: "pointer",
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

// ---- Markdown component styles (DeepSeek-like) ----

const mdFont = '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, "Noto Sans SC", sans-serif';

const h1Style: React.CSSProperties = {
  fontSize: "1.5em",
  fontWeight: 700,
  margin: "28px 0 16px",
  paddingBottom: 10,
  borderBottom: "2px solid #e5e7eb",
  color: "#111827",
  lineHeight: 1.3,
  fontFamily: mdFont,
};
const h2Style: React.CSSProperties = {
  fontSize: "1.3em",
  fontWeight: 700,
  margin: "24px 0 12px",
  color: "#1f2937",
  lineHeight: 1.35,
  fontFamily: mdFont,
};
const h3Style: React.CSSProperties = {
  fontSize: "1.15em",
  fontWeight: 650,
  margin: "20px 0 10px",
  color: "#374151",
  lineHeight: 1.4,
  fontFamily: mdFont,
};
const h4Style: React.CSSProperties = {
  fontSize: "1.05em",
  fontWeight: 600,
  margin: "16px 0 8px",
  color: "#4b5563",
  lineHeight: 1.45,
  fontFamily: mdFont,
};
const pStyle: React.CSSProperties = {
  margin: "0 0 14px 0",
  lineHeight: 1.85,
  color: "#374151",
  fontFamily: mdFont,
};
const ulStyle: React.CSSProperties = {
  paddingLeft: 22,
  margin: "8px 0 14px",
  lineHeight: 1.8,
  color: "#374151",
  fontFamily: mdFont,
};
const olStyle: React.CSSProperties = {
  paddingLeft: 22,
  margin: "8px 0 14px",
  lineHeight: 1.8,
  color: "#374151",
  fontFamily: mdFont,
};
const liStyle: React.CSSProperties = {
  marginBottom: 6,
  lineHeight: 1.75,
};
const inlineCodeStyle: React.CSSProperties = {
  backgroundColor: "#f3f4f6",
  padding: "2px 7px",
  borderRadius: 4,
  fontSize: "0.88em",
  fontFamily: '"SF Mono", "Fira Code", "Fira Mono", Consolas, Monaco, monospace',
  color: "#e11d48",
  border: "1px solid #e5e7eb",
};
// ---- Code block styles (DeepSeek light theme) ----
const codeBlockWrapper: React.CSSProperties = {
  margin: "14px 0",
  borderRadius: 10,
  overflow: "hidden",
  backgroundColor: "#f8fafc",
  border: "1px solid #e2e8f0",
};
const codeBlockBanner: React.CSSProperties = {
  display: "flex",
  justifyContent: "space-between",
  alignItems: "center",
  padding: "8px 14px",
  backgroundColor: "#f1f5f9",
  borderBottom: "1px solid #e2e8f0",
};
const codeLangLabel: React.CSSProperties = {
  fontSize: 12,
  color: "#64748b",
  fontFamily: mdFont,
  fontWeight: 500,
};
const copyBtn: React.CSSProperties = {
  padding: "3px 10px",
  fontSize: 11,
  color: "#475569",
  backgroundColor: "transparent",
  border: "1px solid #cbd5e1",
  borderRadius: 4,
  cursor: "pointer",
  fontFamily: mdFont,
};
const codePre: React.CSSProperties = {
  margin: 0,
  padding: "14px 16px",
  overflow: "auto",
  fontSize: "0.84em",
  lineHeight: 1.65,
  color: "#334155",
  fontFamily: '"SF Mono", "Fira Code", "Fira Mono", Consolas, Monaco, monospace',
  backgroundColor: "transparent",
};

const blockquoteStyle: React.CSSProperties = {
  borderLeft: "4px solid #6366f1",
  paddingLeft: 16,
  margin: "14px 0",
  color: "#4b5563",
  backgroundColor: "#f8fafc",
  padding: "10px 18px",
  borderRadius: "0 6px 6px 0",
  lineHeight: 1.75,
  fontFamily: mdFont,
};
const tableStyle: React.CSSProperties = {
  borderCollapse: "collapse",
  width: "100%",
  margin: "14px 0",
  fontSize: "0.93em",
  fontFamily: mdFont,
  borderRadius: 8,
  overflow: "hidden",
  border: "1px solid #e5e7eb",
};
const thStyle: React.CSSProperties = {
  border: "1px solid #d1d5db",
  padding: "10px 14px",
  backgroundColor: "#f9fafb",
  fontWeight: 650,
  textAlign: "left",
  color: "#111827",
  fontSize: "0.92em",
};
const tdStyle: React.CSSProperties = {
  border: "1px solid #e5e7eb",
  padding: "9px 14px",
  color: "#374151",
};
const hrStyle: React.CSSProperties = {
  border: "none",
  borderTop: "1px solid #e5e7eb",
  margin: "24px 0",
};
const strongStyle: React.CSSProperties = {
  fontWeight: 700,
  color: "#111827",
};
const linkStyle: React.CSSProperties = {
  color: "#2563eb",
  textDecoration: "none",
  borderBottom: "1px solid rgba(37, 99, 235, 0.3)",
};
