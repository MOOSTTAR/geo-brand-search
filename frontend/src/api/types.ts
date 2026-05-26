export interface Task {
  id: string;
  query: string;
  status: "creating" | "executing" | "completed" | "failed";
  progress: number;
  current_step: string | null;
  screenshot_path: string | null;
  response_text: string | null;
  thinking_text: string | null;
  answer_text: string | null;
  answer_html: string | null;
  error_message: string | null;
  created_at: string;
  updated_at: string;
  completed_at: string | null;
}

export interface TaskCreateRequest {
  query: string;
}

export interface WsMessage {
  type: "task_created" | "task_progress" | "task_completed" | "task_failed";
  data: {
    task_id: string;
    status?: string;
    step?: string;
    message?: string;
    progress?: number;
    screenshot_path?: string;
    response_text?: string;
    thinking_text?: string;
    answer_text?: string;
    answer_html?: string;
    error?: string;
    created_at?: string;
    completed_at?: string;
    failed_at?: string;
    timestamp?: string;
  };
}

const API_BASE = "http://localhost:8000";

export async function createTask(query: string): Promise<Task> {
  const res = await fetch(`${API_BASE}/api/tasks`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ query }),
  });
  if (!res.ok) throw new Error("Failed to create task");
  return res.json();
}

export async function fetchTasks(): Promise<Task[]> {
  const res = await fetch(`${API_BASE}/api/tasks`);
  if (!res.ok) throw new Error("Failed to fetch tasks");
  return res.json();
}

export async function fetchTask(taskId: string): Promise<Task> {
  const res = await fetch(`${API_BASE}/api/tasks/${taskId}`);
  if (!res.ok) throw new Error("Failed to fetch task");
  return res.json();
}

export async function deleteTask(taskId: string): Promise<void> {
  const res = await fetch(`${API_BASE}/api/tasks/${taskId}`, {
    method: "DELETE",
  });
  if (!res.ok) throw new Error("Failed to delete task");
}

export function getScreenshotUrl(taskId: string): string {
  return `${API_BASE}/api/tasks/${taskId}/screenshot`;
}
