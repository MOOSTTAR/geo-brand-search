import type { Task } from "../api/types";
import StatusBadge from "./StatusBadge";
import ProgressBar from "./ProgressBar";

interface Props {
  task: Task;
  onViewScreenshot: (taskId: string) => void;
  onViewResponse: (taskId: string) => void;
  onViewRanking: (taskId: string) => void;
  onDelete: (taskId: string) => void;
}

export default function TaskCard({ task, onViewScreenshot, onViewResponse, onViewRanking, onDelete }: Props) {
  const timeStr = task.created_at
    ? new Date(task.created_at).toLocaleString("zh-CN")
    : "";

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
        <div style={{ fontWeight: 500, fontSize: 14, flex: 1, marginRight: 12, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
          {task.query}
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
        <span style={{ fontSize: 12, color: "#bbb" }}>{timeStr}</span>
        <div style={{ display: "flex", gap: 8 }}>
          {task.status === "completed" && task.response_text && (
            <button onClick={() => onViewResponse(task.id)} style={actionBtnStyle("#52c41a")}>
              查看回复
            </button>
          )}
          {task.status === "completed" && task.ranking_table && (
            <button onClick={() => onViewRanking(task.id)} style={actionBtnStyle("#722ed1")}>
              查看排名
            </button>
          )}
          {task.status === "completed" && task.screenshot_path && (
            <button onClick={() => onViewScreenshot(task.id)} style={actionBtnStyle("#1890ff")}>
              查看截图
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
