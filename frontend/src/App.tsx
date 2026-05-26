import { useState, useCallback, useEffect } from "react";
import type { Task, WsMessage } from "./api/types";
import { createTask, fetchTasks, deleteTask } from "./api/types";
import { useWebSocket } from "./hooks/useWebSocket";
import { useScreenshot } from "./hooks/useScreenshot";
import Layout from "./components/Layout";
import SearchInput from "./components/SearchInput";
import TaskList from "./components/TaskList";
import ScreenshotViewer from "./components/ScreenshotViewer";
import ResponseViewer from "./components/ResponseViewer";

export default function App() {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [submitting, setSubmitting] = useState(false);
  const { screenshotUrl, openScreenshot, closeScreenshot } = useScreenshot();
  const [responseText, setResponseText] = useState<string | null>(null);
  const [thinkingText, setThinkingText] = useState<string | null>(null);
  const [answerText, setAnswerText] = useState<string | null>(null);
  const [answerHtml, setAnswerHtml] = useState<string | null>(null);

  useEffect(() => {
    fetchTasks().then(setTasks).catch(console.error);
  }, []);

  const handleWsMessage = useCallback((msg: WsMessage) => {
    const { type, data } = msg;
    if (!data?.task_id) return;

    setTasks((prev) => {
      const idx = prev.findIndex((t) => t.id === data.task_id);

      if (type === "task_created") {
        if (idx >= 0) return prev;
        const newTask: Task = {
          id: data.task_id,
          query: data.query || "",
          status: "creating",
          progress: 0,
          current_step: null,
          screenshot_path: null,
          error_message: null,
          created_at: data.created_at || new Date().toISOString(),
          updated_at: new Date().toISOString(),
          completed_at: null,
        };
        return [newTask, ...prev];
      }

      if (idx < 0) return prev;

      const updated = [...prev];
      const task = { ...updated[idx] };

      if (type === "task_progress") {
        task.status = (data.status as Task["status"]) || "executing";
        task.progress = data.progress ?? task.progress;
        task.current_step = data.message ?? task.current_step;
      } else if (type === "task_completed") {
        task.status = "completed";
        task.progress = 100;
        task.screenshot_path = data.screenshot_path ?? null;
        task.response_text = data.response_text ?? null;
        task.thinking_text = data.thinking_text ?? null;
        task.answer_text = data.answer_text ?? null;
        task.answer_html = data.answer_html ?? null;
        task.completed_at = data.completed_at ?? new Date().toISOString();
      } else if (type === "task_failed") {
        task.status = "failed";
        task.error_message = data.error ?? "Unknown error";
      }

      task.updated_at = data.timestamp ?? new Date().toISOString();
      updated[idx] = task;
      return updated;
    });
  }, []);

  const { isConnected } = useWebSocket(handleWsMessage);

  const handleSubmit = useCallback(async (query: string) => {
    setSubmitting(true);
    try {
      await createTask(query);
    } finally {
      setSubmitting(false);
    }
  }, []);

  const handleDelete = useCallback(async (taskId: string) => {
    try {
      await deleteTask(taskId);
      setTasks((prev) => prev.filter((t) => t.id !== taskId));
    } catch (err) {
      console.error("Delete failed:", err);
    }
  }, []);

  return (
    <Layout wsConnected={isConnected}>
      <SearchInput onSubmit={handleSubmit} disabled={submitting} />
      <TaskList
        tasks={tasks}
        onViewScreenshot={openScreenshot}
        onViewResponse={(taskId) => {
          const task = tasks.find((t) => t.id === taskId);
          if (task?.response_text) {
            setResponseText(task.response_text);
            setThinkingText(task.thinking_text ?? null);
            setAnswerText(task.answer_text ?? null);
            setAnswerHtml(task.answer_html ?? null);
          }
        }}
        onDelete={handleDelete}
      />
      <ScreenshotViewer url={screenshotUrl} onClose={closeScreenshot} />
      <ResponseViewer
        text={responseText}
        thinkingText={thinkingText}
        answerText={answerText}
        answerHtml={answerHtml}
        onClose={() => { setResponseText(null); setThinkingText(null); setAnswerText(null); setAnswerHtml(null); }}
      />
    </Layout>
  );
}
