import { useState, useCallback, useEffect, useRef } from "react";
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
import TechBackground from "./components/TechBackground";

function parsePath(): string | null {
  const seg = window.location.pathname.replace(/^\/+|\/+$/g, "");
  return seg || null;
}

export default function App() {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [submitting, setSubmitting] = useState(false);
  const [activeTab, setActiveTab] = useState(() => parsePath() ? "tasks" : "search");
  const [detailTaskId, setDetailTaskId] = useState<string | null>(parsePath);
  const { screenshotUrl, openScreenshot, closeScreenshot } = useScreenshot();
  const [responseText, setResponseText] = useState<string | null>(null);
  const [thinkingText, setThinkingText] = useState<string | null>(null);
  const [answerText, setAnswerText] = useState<string | null>(null);
  const [answerHtml, setAnswerHtml] = useState<string | null>(null);
  const [rankingTable, setRankingTable] = useState<string | null>(null);

  // Intro / scroll progress
  const hasPath = parsePath() !== null;
  const [introDone, setIntroDone] = useState(false);
  const [scrollProgress, setScrollProgress] = useState(hasPath ? 1 : 0);
  const [scaleProgress, setScaleProgress] = useState(hasPath ? 1 : 0);
  const animRef = useRef<number>(0);

  // Block scroll during splash
  useEffect(() => {
    if (hasPath || scrollProgress >= 1) return;
    document.body.style.overflow = "hidden";
    return () => { document.body.style.overflow = ""; };
  }, [hasPath, scrollProgress]);

  // easeOutBack: overshoot then settle
  function easeOutBack(t: number): number {
    const c1 = 1.2;
    return 1 + (c1 + 1) * Math.pow(t - 1, 3) + c1 * Math.pow(t - 1, 2);
  }
  function easeOutCubic(t: number): number {
    return 1 - Math.pow(1 - t, 3);
  }

  // Click to animate scroll
  const handleEnter = useCallback(() => {
    if (!introDone) return;
    const start = performance.now();
    const duration = 1000;
    const tick = (now: number) => {
      const raw = Math.min((now - start) / duration, 1);
      const pos = easeOutBack(raw);
      const scl = easeOutCubic(raw); // scale leads, no overshoot
      setScrollProgress(pos);
      setScaleProgress(scl);
      if (raw < 1) animRef.current = requestAnimationFrame(tick);
      else document.body.style.overflow = "";
    };
    animRef.current = requestAnimationFrame(tick);
  }, [introDone]);

  useEffect(() => {
    return () => { if (animRef.current) cancelAnimationFrame(animRef.current); };
  }, []);

  useEffect(() => {
    fetchTasks().then(setTasks).catch(console.error);
  }, []);

  // Sync URL
  useEffect(() => {
    const target = detailTaskId ? "/" + detailTaskId : "/";
    if (window.location.pathname !== target) {
      window.history.pushState(null, "", target);
    }
    const onPop = () => {
      const id = parsePath();
      setDetailTaskId(id);
      if (id) setActiveTab("tasks");
    };
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
          id: data.task_id, query: data.query || "", status: "creating", progress: 0,
          current_step: null, screenshot_path: null, response_text: null,
          thinking_text: null, answer_text: null, answer_html: null,
          ranking_table: null, brand_keyword: data.brand_keyword ?? null,
          brand_rank: null, sources_json: null, error_message: null,
          created_at: data.created_at || new Date().toISOString(),
          updated_at: new Date().toISOString(), completed_at: null,
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
        task.status = "completed"; task.progress = 100;
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

  const handleSubmit = useCallback(async (_query: string, _brandKeyword: string, _platforms: string[]) => {
    setSubmitting(true);
    try {
      await createTask(_query, _brandKeyword || undefined);
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
    } catch { showToast("删除失败", "error"); }
  }, [detailTaskId]);

  const handleViewDetail = useCallback((taskId: string) => {
    setDetailTaskId(taskId); setActiveTab("tasks");
  }, []);

  const handleBack = useCallback(() => setDetailTaskId(null), []);

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
    if (task?.ranking_table) setRankingTable(task.ranking_table);
  }, [tasks]);

  const handleTabChange = useCallback((key: string) => {
    setActiveTab(key);
    if (key !== "tasks") setDetailTaskId(null);
  }, []);

  const showApp = hasPath || scrollProgress >= 1;

  return (
    <div style={{ position: "relative" }}>
      {/* 3D GEO — always visible */}
      <TechBackground
        visible={true}
        intro={!hasPath}
        scrollProgress={scrollProgress}
        scaleProgress={scaleProgress}
        onIntroDone={() => setIntroDone(true)}
      />

      {/* Splash text indicators */}
      {!hasPath && scrollProgress < 1 && (
        <div style={{
          position: "fixed", inset: 0, zIndex: 10,
          display: "flex", flexDirection: "column",
          alignItems: "center", justifyContent: "center",
          opacity: 1 - scrollProgress,
          transition: "opacity 0.2s",
        }}>
          {introDone && (
            <button
              onClick={handleEnter}
              style={{
                display: "flex", flexDirection: "column",
                alignItems: "center", gap: 10, marginTop: "55vh",
                background: "none", border: "none", cursor: "pointer",
                animation: "fade-in 0.8s ease",
              }}>
              <span style={{ fontSize: 14, color: "rgba(255,255,255,0.6)", letterSpacing: 2 }}>
                开启探索
              </span>
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="rgba(255,255,255,0.35)" strokeWidth="2"
                style={{ animation: "float-arrow 2s ease-in-out infinite" }}>
                <path d="M12 5v14M5 12l7 7 7-7" />
              </svg>
            </button>
          )}
        </div>
      )}

      {/* App content */}
      <div style={{
        opacity: showApp ? 1 : 0,
        transition: "opacity 0.5s ease",
        pointerEvents: showApp ? "auto" : "none",
      }}>
        <Layout wsConnected={isConnected} activeTab={activeTab} onTabChange={handleTabChange}>
          {activeTab === "search" && <SearchInput onSubmit={handleSubmit} disabled={submitting} />}
          {activeTab === "tasks" && (
            detailTask ? (
              <TaskDetail task={detailTask} onViewScreenshot={openScreenshot}
                onViewResponse={handleViewResponse} onViewRanking={handleViewRanking}
                onBack={handleBack} />
            ) : (
              <TaskList tasks={tasks} onViewDetail={handleViewDetail} onDelete={handleDelete} />
            )
          )}
          {activeTab === "profile" && (
            <div style={{ textAlign: "center", padding: 80, color: "#999", fontSize: 15,
              backgroundColor: "#fff", borderRadius: 8, border: "1px solid #f0f0f0" }}>
              暂未开发
            </div>
          )}
        </Layout>
      </div>

      <ScreenshotViewer url={screenshotUrl} onClose={closeScreenshot} />
      <ResponseViewer text={responseText} thinkingText={thinkingText}
        answerText={answerText} answerHtml={answerHtml}
        onClose={() => { setResponseText(null); setThinkingText(null); setAnswerText(null); setAnswerHtml(null); }} />
      <RankingViewer rankingTable={rankingTable} onClose={() => setRankingTable(null)} />
      <ToastContainer />
    </div>
  );
}
