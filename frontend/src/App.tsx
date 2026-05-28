import { useState, useCallback, useEffect } from "react";
import type { Task, WsMessage } from "./api/types";
import { createTask, fetchTasks, deleteTask } from "./api/types";
import { useWebSocket } from "./hooks/useWebSocket";
import { useScreenshot } from "./hooks/useScreenshot";
import Layout from "./components/Layout";
import SearchInput from "./components/SearchInput";
import TaskList from "./components/TaskList";
import TaskDetail from "./components/TaskDetail";
import ScreenshotViewer from "./components/ScreenshotViewer";
import ResponseViewer from "./components/ResponseViewer";
import RankingViewer from "./components/RankingViewer";
import ToastContainer, { showToast } from "./components/Toast";

function parsePath(): string | null {
  const seg = window.location.pathname.replace(/^\/+|\/+$/g, "");
  return seg || null;
}

export default function App() {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [submitting, setSubmitting] = useState(false);
  const [detailTaskId, setDetailTaskId] = useState<string | null>(parsePath);
  const { screenshotUrl, openScreenshot, closeScreenshot } = useScreenshot();
  const [responseText, setResponseText] = useState<string | null>(null);
  const [thinkingText, setThinkingText] = useState<string | null>(null);
  const [answerText, setAnswerText] = useState<string | null>(null);
  const [answerHtml, setAnswerHtml] = useState<string | null>(null);
  const [rankingTable, setRankingTable] = useState<string | null>(null);

  useEffect(() => {
    fetchTasks().then(setTasks).catch(console.error);
  }, []);

  // Sync URL ↔ detailTaskId
  useEffect(() => {
    const target = detailTaskId ? "/" + detailTaskId : "/";
    if (window.location.pathname !== target) {
      window.history.pushState(null, "", target);
    }

    const onPop = () => setDetailTaskId(parsePath());
    window.addEventListener("popstate", onPop);
    return () => window.removeEventListener("popstate", onPop);
  }, [detailTaskId]);

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
          response_text: null,
          thinking_text: null,
          answer_text: null,
          answer_html: null,
          ranking_table: null,
          brand_keyword: data.brand_keyword ?? null,
          brand_rank: null,
          sources_json: null,
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
        task.ranking_table = data.ranking_table ?? null;
        task.brand_keyword = data.brand_keyword ?? null;
        task.brand_rank = data.brand_rank ?? null;
        task.sources_json = data.sources_json ?? null;
        task.completed_at = data.completed_at ?? new Date().toISOString();
      } else if (type === "task_failed") {
        task.status = "failed";
        task.error_message = data.error ?? "Unknown error";
      } else if (type === "task_ranking") {
        task.ranking_table = data.ranking_table ?? null;
      }

      task.updated_at = data.timestamp ?? new Date().toISOString();
      updated[idx] = task;
      return updated;
    });
  }, []);

  const { isConnected } = useWebSocket(handleWsMessage);

  const handleSubmit = useCallback(async (query: string, brandKeyword: string) => {
    setSubmitting(true);
    try {
      await createTask(query, brandKeyword || undefined);
      showToast("任务已创建", "success");
    } catch {
      showToast("创建任务失败", "error");
    } finally {
      setSubmitting(false);
    }
  }, []);

  const handleDelete = useCallback(async (taskId: string) => {
    try {
      await deleteTask(taskId);
      setTasks((prev) => prev.filter((t) => t.id !== taskId));
      if (detailTaskId === taskId) setDetailTaskId(null);
      showToast("删除成功", "success");
    } catch (err) {
      showToast("删除失败", "error");
    }
  }, [detailTaskId]);

  const detailTask = detailTaskId ? tasks.find((t) => t.id === detailTaskId) ?? null : null;

  const handleViewResponse = useCallback((taskId: string) => {
    const task = tasks.find((t) => t.id === taskId);
    if (task?.response_text) {
      setResponseText(task.response_text);
      setThinkingText(task.thinking_text ?? null);
      setAnswerText(task.answer_text ?? null);
      setAnswerHtml(task.answer_html ?? null);
    }
  }, [tasks]);

  const handleViewRanking = useCallback((taskId: string) => {
    const task = tasks.find((t) => t.id === taskId);
    if (task?.ranking_table) {
      setRankingTable(task.ranking_table);
    }
  }, [tasks]);

  return (
    <Layout wsConnected={isConnected}>
      {detailTask ? (
        <TaskDetail
          task={detailTask}
          onViewScreenshot={openScreenshot}
          onViewResponse={handleViewResponse}
          onViewRanking={handleViewRanking}
          onBack={() => setDetailTaskId(null)}
        />
      ) : (
        <>
          <SearchInput onSubmit={handleSubmit} disabled={submitting} />
          <TaskList
            tasks={tasks}
            onViewDetail={setDetailTaskId}
            onDelete={handleDelete}
          />
        </>
      )}
      <ScreenshotViewer url={screenshotUrl} onClose={closeScreenshot} />
      <ResponseViewer
        text={responseText}
        thinkingText={thinkingText}
        answerText={answerText}
        answerHtml={answerHtml}
        onClose={() => { setResponseText(null); setThinkingText(null); setAnswerText(null); setAnswerHtml(null); }}
      />
      <RankingViewer
        rankingTable={rankingTable}
        onClose={() => setRankingTable(null)}
      />
      <ToastContainer />
    </Layout>
  );
}
