import type { Task } from "../api/types";
import StatusBadge from "./StatusBadge";
import ProgressBar from "./ProgressBar";

interface Props {
  task: Task;
  onViewDetail: (taskId: string) => void;
  onDelete: (taskId: string) => void;
}

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

  return (
    <div
      style={{
        padding: "16px 20px",
        backgroundColor: "#fff",
        borderRadius: 8,
        border: "1px solid #f0f0f0",
        marginBottom: 12,
        transition: "box-shadow 0.2s",
      }}
      onMouseEnter={(e) => (e.currentTarget.style.boxShadow = "0 2px 8px rgba(0,0,0,0.08)")}
      onMouseLeave={(e) => (e.currentTarget.style.boxShadow = "none")}
    >
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 10 }}>
        <div style={{ display: "flex", alignItems: "center", gap: 8, flex: 1, marginRight: 12, overflow: "hidden" }}>
          <span style={{ fontWeight: 500, fontSize: 14, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
            {task.query}
          </span>
          {task.brand_keyword && (
            <span style={{
              fontSize: 12,
              color: "#1677ff",
              backgroundColor: "#e6f4ff",
              border: "1px solid #91caff",
              borderRadius: 4,
              padding: "1px 8px",
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
            <div style={{ fontSize: 12, color: "#999", marginTop: 4 }}>
              {task.current_step}
            </div>
          )}
        </div>
      )}

      {task.status === "failed" && task.error_message && (
        <div style={{ fontSize: 12, color: "#ff4d4f", marginBottom: 8, padding: "4px 8px", backgroundColor: "#fff2f0", borderRadius: 4 }}>
          {task.error_message}
        </div>
      )}

      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <div style={{ display: "flex", gap: 16, alignItems: "center" }}>
          <span style={{ fontSize: 12, color: "#bbb" }}>{timeStr}</span>
          {duration && (
            <span style={{ fontSize: 12, color: "#8c8c8c" }}>
              用时: {duration}
            </span>
          )}
        </div>
        <div style={{ display: "flex", gap: 8 }}>
          {task.status === "completed" && (
            <button onClick={() => onViewDetail(task.id)} style={actionBtnStyle("#722ed1")}>
              查看详情
            </button>
          )}
          <button onClick={() => onDelete(task.id)} style={actionBtnStyle("#ff4d4f")}>
            删除
          </button>
        </div>
      </div>
    </div>
  );
}

function actionBtnStyle(color: string): React.CSSProperties {
  return {
    padding: "4px 12px",
    fontSize: 12,
    color,
    backgroundColor: "transparent",
    border: `1px solid ${color}`,
    borderRadius: 4,
    cursor: "pointer",
    transition: "all 0.2s",
  };
}
