import type { Task } from "../api/types";
import StatusBadge from "./StatusBadge";
import ProgressBar from "./ProgressBar";

interface Props {
  task: Task;
  onViewDetail: (taskId: string) => void;
  onDelete: (taskId: string) => void;
}

const STATUS_ACCENT: Record<string, string> = {
  creating: "#d1d5db",
  executing: "#5b5ef7",
  completed: "#10b981",
  failed: "#ef4444",
};

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

export default function TaskCard({ task, onViewDetail, onDelete }: Props) {
  const timeStr = task.created_at
    ? new Date(task.created_at).toLocaleString("zh-CN")
    : "";
  const duration = calcDuration(task.created_at, task.completed_at);
  const accent = STATUS_ACCENT[task.status] ?? "#d1d5db";

  return (
    <div
      className="card-hover"
      style={{
        padding: "16px 20px",
        backgroundColor: "var(--color-surface)",
        borderRadius: "var(--radius-md)",
        border: "1px solid var(--color-border)",
        borderLeft: `3px solid ${accent}`,
        marginBottom: 12,
        animation: "slide-up 0.35s ease both",
      }}
    >
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 10 }}>
        <div style={{ display: "flex", alignItems: "center", gap: 8, flex: 1, marginRight: 12, overflow: "hidden" }}>
          <span style={{ fontWeight: 600, fontSize: 14, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap", color: "var(--color-text)" }}>
            {task.query}
          </span>
          {task.brand_keyword && (
            <span style={{
              fontSize: 11,
              fontWeight: 600,
              color: "var(--color-primary)",
              backgroundColor: "var(--color-primary-light)",
              borderRadius: 10,
              padding: "2px 10px",
              whiteSpace: "nowrap",
              flexShrink: 0,
            }}>
              品牌: {task.brand_keyword}
            </span>
          )}
        </div>
        <StatusBadge status={task.status} />
      </div>

      {task.status === "executing" && (
        <div style={{ marginBottom: 8 }}>
          <ProgressBar progress={task.progress} />
          {task.current_step && (
            <div style={{ fontSize: 12, color: "var(--color-text-muted)", marginTop: 6 }}>
              {task.current_step}
            </div>
          )}
        </div>
      )}

      {task.status === "failed" && task.error_message && (
        <div style={{
          fontSize: 12,
          color: "var(--color-error)",
          marginBottom: 8,
          padding: "6px 10px",
          backgroundColor: "var(--color-error-light)",
          borderRadius: "var(--radius-sm)",
          fontWeight: 500,
        }}>
          {task.error_message}
        </div>
      )}

      {task.status === "completed" && task.brand_rank && (
        <div style={{
          fontSize: 12,
          color: "var(--color-primary)",
          marginBottom: 8,
          padding: "6px 10px",
          backgroundColor: "var(--color-primary-light)",
          borderRadius: "var(--radius-sm)",
          lineHeight: 1.7,
          whiteSpace: "pre-line",
          fontWeight: 500,
        }}>
          {task.brand_rank}
        </div>
      )}

      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <div style={{ display: "flex", gap: 16, alignItems: "center" }}>
          <span style={{ fontSize: 12, color: "var(--color-text-muted)" }}>{timeStr}</span>
          {duration && (
            <span style={{ fontSize: 12, color: "var(--color-text-secondary)", fontWeight: 500 }}>
              用时 {duration}
            </span>
          )}
        </div>
        <div style={{ display: "flex", gap: 8 }}>
          {task.status === "completed" && (
            <button onClick={() => onViewDetail(task.id)} style={btnStyle("var(--color-primary)")}>
              查看详情
            </button>
          )}
          <button onClick={() => onDelete(task.id)} style={btnStyle("var(--color-error)")}>
            删除
          </button>
        </div>
      </div>
    </div>
  );
}

function btnStyle(color: string): React.CSSProperties {
  return {
    padding: "5px 14px",
    fontSize: 12,
    fontWeight: 500,
    color,
    backgroundColor: "transparent",
    border: `1.5px solid ${color}`,
    borderRadius: 20,
    cursor: "pointer",
    transition: "all var(--transition)",
  };
}
