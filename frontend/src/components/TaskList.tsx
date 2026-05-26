import type { Task } from "../api/types";
import TaskCard from "./TaskCard";
import EmptyState from "./EmptyState";

interface Props {
  tasks: Task[];
  onViewScreenshot: (taskId: string) => void;
  onViewResponse: (taskId: string) => void;
  onViewRanking: (taskId: string) => void;
  onDelete: (taskId: string) => void;
}

export default function TaskList({ tasks, onViewScreenshot, onViewResponse, onViewRanking, onDelete }: Props) {
  if (tasks.length === 0) {
    return <EmptyState />;
  }

  return (
    <div>
      <div style={{ fontSize: 13, color: "#999", marginBottom: 12 }}>
        共 {tasks.length} 个任务
      </div>
      {tasks.map((task) => (
        <TaskCard
          key={task.id}
          task={task}
          onViewScreenshot={onViewScreenshot}
          onViewResponse={onViewResponse}
          onViewRanking={onViewRanking}
          onDelete={onDelete}
        />
      ))}
    </div>
  );
}
