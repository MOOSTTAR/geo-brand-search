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
          color: "#1890ff",
          cursor: "pointer",
          padding: 0,
          marginBottom: 16,
          display: "flex",
          alignItems: "center",
          gap: 4,
        }}
      >
        ← 返回列表
      </button>

      {/* Header */}
      <div style={{
        backgroundColor: "#fff",
        borderRadius: 8,
        border: "1px solid #f0f0f0",
        padding: "20px 24px",
        marginBottom: 16,
      }}>
        <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 8 }}>
          <span style={{ fontSize: 18, fontWeight: 600 }}>{task.query}</span>
          {task.brand_keyword && (
            <span style={{
              fontSize: 12,
              color: "#1677ff",
              backgroundColor: "#e6f4ff",
              border: "1px solid #91caff",
              borderRadius: 4,
              padding: "1px 8px",
              whiteSpace: "nowrap",
            }}>
              品牌: {task.brand_keyword}
            </span>
          )}
        </div>

        {/* Brand rank */}
        {task.brand_rank && (
          <div style={{
            fontSize: 15,
            fontWeight: 500,
            color: "#722ed1",
            backgroundColor: "#f9f0ff",
            border: "1px solid #d3adf7",
            borderRadius: 6,
            padding: "8px 16px",
            marginBottom: 12,
            display: "inline-block",
            whiteSpace: "pre-line",
            lineHeight: 1.8,
          }}>
            {task.brand_rank}
          </div>
        )}

        {/* Meta info */}
        <div style={{ display: "flex", gap: 24, fontSize: 13, color: "#666" }}>
          <span><span style={{ color: "#999" }}>创建时间: </span>{timeStr}</span>
          {duration && <span><span style={{ color: "#999" }}>任务用时: </span>{duration}</span>}
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
              style={{
                display: "flex",
                gap: 12,
                padding: "14px 16px",
                backgroundColor: "#fff",
                borderRadius: 8,
                border: "1px solid #f0f0f0",
                marginBottom: 8,
                textDecoration: "none",
                color: "inherit",
                transition: "box-shadow 0.2s",
              }}
              onMouseEnter={(e) => (e.currentTarget.style.boxShadow = "0 2px 8px rgba(0,0,0,0.08)")}
              onMouseLeave={(e) => (e.currentTarget.style.boxShadow = "none")}
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
                    color: "#999",
                    backgroundColor: "#f5f5f5",
                    borderRadius: 3,
                    padding: "0 4px",
                    lineHeight: "16px",
                    textAlign: "center",
                  }}>
                    [{src.cite}]
                  </span>
                )}
              </div>

              <div style={{ flex: 1, minWidth: 0 }}>
                <div style={{ display: "flex", alignItems: "baseline", gap: 8, marginBottom: 4, flexWrap: "wrap" }}>
                  <span style={{ fontSize: 14, fontWeight: 500, color: "#1a1a1a", lineHeight: 1.4 }}>
                    {src.title || src.url}
                  </span>
                </div>

                <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 4 }}>
                  {src.site_name && (
                    <span style={{ fontSize: 12, color: "#8c8c8c" }}>{src.site_name}</span>
                  )}
                  {src.date && (
                    <span style={{ fontSize: 12, color: "#bbb" }}>{src.date}</span>
                  )}
                </div>

                {src.snippet && (
                  <div style={{ fontSize: 12, color: "#999", lineHeight: 1.5, overflow: "hidden", textOverflow: "ellipsis", display: "-webkit-box", WebkitLineClamp: 2, WebkitBoxOrient: "vertical" }}>
                    {src.snippet}
                  </div>
                )}

                <div style={{ fontSize: 11, color: "#bbb", marginTop: 2, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
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
    padding: "6px 16px",
    fontSize: 13,
    color,
    backgroundColor: "transparent",
    border: `1px solid ${color}`,
    borderRadius: 4,
    cursor: "pointer",
  };
}

function pageBtnStyle(disabled: boolean): React.CSSProperties {
  return {
    padding: "4px 12px",
    fontSize: 12,
    color: disabled ? "#d9d9d9" : "#1890ff",
    backgroundColor: "transparent",
    border: `1px solid ${disabled ? "#d9d9d9" : "#1890ff"}`,
    borderRadius: 4,
    cursor: disabled ? "not-allowed" : "pointer",
  };
}
