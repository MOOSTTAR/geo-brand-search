import { useState } from "react";
import type { Task } from "../api/types";

interface SourceItem {
  logo: string;
  site_name: string;
  title: string;
  url: string;
  date: string;
  snippet: string;
  cite: string;
}

interface Props {
  task: Task;
  onViewScreenshot: (taskId: string) => void;
  onViewResponse: (taskId: string) => void;
  onViewRanking: (taskId: string) => void;
  onBack: () => void;
}

const PAGE_SIZE = 10;

function calcDuration(created: string, completed: string | null): string {
  if (!completed) return "";
  const ms = new Date(completed).getTime() - new Date(created).getTime();
  if (ms < 0) return "";
  const s = Math.floor(ms / 1000);
  if (s < 60) return `${s}秒`;
  const m = Math.floor(s / 60);
  const remainS = s % 60;
  if (m < 60) return `${m}分${remainS}秒`;
  const h = Math.floor(m / 60);
  const remainM = m % 60;
  return `${h}时${remainM}分${remainS}秒`;
}

function parseSources(json: string | null): SourceItem[] {
  if (!json) return [];
  try {
    return JSON.parse(json);
  } catch {
    return [];
  }
}

export default function TaskDetail({ task, onViewScreenshot, onViewResponse, onViewRanking, onBack }: Props) {
  const duration = calcDuration(task.created_at, task.completed_at);
  const timeStr = new Date(task.created_at).toLocaleString("zh-CN");
  const sources = parseSources(task.sources_json);
  const [page, setPage] = useState(0);

  const totalPages = Math.ceil(sources.length / PAGE_SIZE);
  const pageSources = sources.slice(page * PAGE_SIZE, (page + 1) * PAGE_SIZE);

  return (
    <div style={{ maxWidth: 800, margin: "0 auto" }}>
      {/* Back button */}
      <button
        onClick={onBack}
        style={{
          background: "none",
          border: "none",
          fontSize: 14,
          color: "var(--color-primary)",
          cursor: "pointer",
          padding: 0,
          marginBottom: 16,
          display: "flex",
          alignItems: "center",
          gap: 4,
          fontWeight: 500,
          transition: "opacity var(--transition)",
        }}
        onMouseEnter={(e) => (e.currentTarget.style.opacity = "0.7")}
        onMouseLeave={(e) => (e.currentTarget.style.opacity = "1")}
      >
        ← 返回列表
      </button>

      {/* Header */}
      <div style={{
        backgroundColor: "var(--color-surface)",
        borderRadius: "var(--radius-lg)",
        border: "1px solid var(--color-border)",
        padding: "24px 28px",
        marginBottom: 16,
        boxShadow: "var(--shadow-sm)",
        animation: "slide-down 0.3s ease",
      }}>
        <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 8 }}>
          <span style={{ fontSize: 18, fontWeight: 700, color: "var(--color-text)" }}>{task.query}</span>
          {task.brand_keyword && (
            <span style={{
              fontSize: 12,
              fontWeight: 600,
              color: "var(--color-primary)",
              backgroundColor: "var(--color-primary-light)",
              borderRadius: 10,
              padding: "3px 12px",
              whiteSpace: "nowrap",
            }}>
              品牌: {task.brand_keyword}
            </span>
          )}
        </div>

        {/* Brand rank */}
        {task.brand_rank && (
          <div style={{
            fontSize: 14,
            fontWeight: 600,
            color: "var(--color-primary)",
            background: "linear-gradient(135deg, #f5f4ff, #ede9fe)",
            borderRadius: "var(--radius-md)",
            padding: "10px 18px",
            marginBottom: 12,
            display: "inline-block",
            whiteSpace: "pre-line",
            lineHeight: 1.9,
          }}>
            {task.brand_rank}
          </div>
        )}

        {/* Meta info */}
        <div style={{ display: "flex", gap: 24, fontSize: 13, color: "var(--color-text-secondary)" }}>
          <span>创建 {timeStr}</span>
          {duration && <span>用时 {duration}</span>}
        </div>

        {/* Action buttons */}
        <div style={{ display: "flex", gap: 10, flexWrap: "wrap", marginTop: 16, paddingTop: 16, borderTop: "1px solid #f0f0f0" }}>
          {task.response_text && (
            <button onClick={() => onViewResponse(task.id)} style={detailBtnStyle("#52c41a")}>
              查看回复
            </button>
          )}
          {task.ranking_table && (
            <button onClick={() => onViewRanking(task.id)} style={detailBtnStyle("#722ed1")}>
              查看所有排名
            </button>
          )}
          {task.screenshot_path && (
            <button onClick={() => onViewScreenshot(task.id)} style={detailBtnStyle("#1890ff")}>
              查看截图
            </button>
          )}
        </div>
      </div>

      {/* Source list */}
      {sources.length > 0 && (
        <div>
          <h3 style={{ fontSize: 16, fontWeight: 600, marginBottom: 12, color: "#333" }}>
            信源列表 ({sources.length})
          </h3>

          {pageSources.map((src, i) => (
            <a
              key={page * PAGE_SIZE + i}
              href={src.url}
              target="_blank"
              rel="noopener noreferrer"
              className="card-hover"
              style={{
                display: "flex",
                gap: 12,
                padding: "14px 16px",
                backgroundColor: "var(--color-surface)",
                borderRadius: "var(--radius-md)",
                border: "1px solid var(--color-border)",
                marginBottom: 8,
                textDecoration: "none",
                color: "inherit",
                animation: "slide-up 0.3s ease both",
                animationDelay: `${i * 0.03}s`,
              }}
            >
              {/* Logo + cite column */}
              <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 4, flexShrink: 0, minWidth: 28 }}>
                {src.logo ? (
                  <img
                    src={src.logo}
                    alt=""
                    style={{ width: 24, height: 24, borderRadius: 4 }}
                    onError={(e) => { (e.target as HTMLImageElement).style.display = "none"; }}
                  />
                ) : (
                  <div style={{ width: 24, height: 24 }} />
                )}
                {src.cite && (
                  <span style={{
                    fontSize: 10,
                    fontWeight: 600,
                    color: "var(--color-text-muted)",
                    backgroundColor: "#f3f4f6",
                    borderRadius: 8,
                    padding: "1px 6px",
                    lineHeight: "16px",
                    textAlign: "center",
                  }}>
                    [{src.cite}]
                  </span>
                )}
              </div>

              <div style={{ flex: 1, minWidth: 0 }}>
                <div style={{ display: "flex", alignItems: "baseline", gap: 8, marginBottom: 4, flexWrap: "wrap" }}>
                  <span style={{ fontSize: 14, fontWeight: 600, color: "var(--color-text)", lineHeight: 1.4 }}>
                    {src.title || src.url}
                  </span>
                </div>

                <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 4 }}>
                  {src.site_name && (
                    <span style={{ fontSize: 12, color: "var(--color-text-secondary)", fontWeight: 500 }}>{src.site_name}</span>
                  )}
                  {src.date && (
                    <span style={{ fontSize: 12, color: "var(--color-text-muted)" }}>{src.date}</span>
                  )}
                </div>

                {src.snippet && (
                  <div style={{ fontSize: 12, color: "var(--color-text-secondary)", lineHeight: 1.5, overflow: "hidden", textOverflow: "ellipsis", display: "-webkit-box", WebkitLineClamp: 2, WebkitBoxOrient: "vertical" }}>
                    {src.snippet}
                  </div>
                )}

                <div style={{ fontSize: 11, color: "var(--color-text-muted)", marginTop: 2, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                  {src.url}
                </div>
              </div>
            </a>
          ))}

          {/* Pagination controls */}
          {totalPages > 1 && (
            <div style={{ display: "flex", justifyContent: "center", alignItems: "center", gap: 12, marginTop: 16, marginBottom: 8 }}>
              <button
                onClick={() => setPage(0)}
                disabled={page === 0}
                style={pageBtnStyle(page === 0)}
              >
                首页
              </button>
              <button
                onClick={() => setPage(p => p - 1)}
                disabled={page === 0}
                style={pageBtnStyle(page === 0)}
              >
                上一页
              </button>
              <span style={{ fontSize: 13, color: "#666" }}>
                第 {page + 1} / {totalPages} 页
              </span>
              <button
                onClick={() => setPage(p => p + 1)}
                disabled={page >= totalPages - 1}
                style={pageBtnStyle(page >= totalPages - 1)}
              >
                下一页
              </button>
              <button
                onClick={() => setPage(totalPages - 1)}
                disabled={page >= totalPages - 1}
                style={pageBtnStyle(page >= totalPages - 1)}
              >
                末页
              </button>
            </div>
          )}
        </div>
      )}

      {task.status === "completed" && sources.length === 0 && (
        <div style={{ textAlign: "center", color: "#999", fontSize: 14, padding: 32 }}>
          暂无信源数据
        </div>
      )}
    </div>
  );
}

function detailBtnStyle(color: string): React.CSSProperties {
  return {
    padding: "7px 18px",
    fontSize: 13,
    fontWeight: 500,
    color,
    backgroundColor: "transparent",
    border: `1.5px solid ${color}`,
    borderRadius: 20,
    cursor: "pointer",
    transition: "all var(--transition)",
  };
}

function pageBtnStyle(disabled: boolean): React.CSSProperties {
  return {
    padding: "5px 14px",
    fontSize: 12,
    fontWeight: 500,
    color: disabled ? "var(--color-text-muted)" : "var(--color-primary)",
    backgroundColor: "transparent",
    border: `1.5px solid ${disabled ? "var(--color-border)" : "var(--color-primary)"}`,
    borderRadius: 20,
    cursor: disabled ? "not-allowed" : "pointer",
    transition: "all var(--transition)",
  };
}
