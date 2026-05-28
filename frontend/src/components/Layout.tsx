import type { ReactNode } from "react";

export const TABS = [
  { key: "search", label: "查询品牌" },
  { key: "tasks", label: "查看任务" },
  { key: "profile", label: "个人中心" },
] as const;

interface Props {
  wsConnected: boolean;
  activeTab: string;
  onTabChange: (key: string) => void;
  children: ReactNode;
}

export default function Layout({ wsConnected, activeTab, onTabChange, children }: Props) {
  return (
    <div style={{ minHeight: "100vh", backgroundColor: "var(--color-bg)" }}>
      <header
        style={{
          padding: "0 24px",
          height: 54,
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          background: "linear-gradient(135deg, #ffffff 0%, #fafaff 100%)",
          borderBottom: "1px solid var(--color-border)",
          position: "relative",
          zIndex: 100,
        }}
      >
        <h1 style={{
          fontSize: 18,
          fontWeight: 700,
          margin: 0,
          background: "var(--color-primary-gradient)",
          WebkitBackgroundClip: "text",
          WebkitTextFillColor: "transparent",
          whiteSpace: "nowrap",
        }}>
          GEO 品牌查询
        </h1>

        <nav style={{
          display: "flex",
          gap: 4,
          height: 54,
          position: "absolute",
          left: "50%",
          transform: "translateX(-50%)",
          alignItems: "center",
        }}>
          {TABS.map((tab) => {
            const isActive = activeTab === tab.key;
            return (
              <button
                key={tab.key}
                onClick={() => onTabChange(tab.key)}
                style={{
                  padding: "6px 22px",
                  fontSize: 14,
                  fontWeight: isActive ? 600 : 400,
                  color: isActive ? "#fff" : "var(--color-text-secondary)",
                  backgroundColor: isActive ? "var(--color-primary)" : "transparent",
                  border: "none",
                  borderRadius: 20,
                  cursor: "pointer",
                  transition: "all var(--transition)",
                  whiteSpace: "nowrap",
                  position: "relative",
                }}
              >
                {tab.label}
                {isActive && (
                  <span style={{
                    position: "absolute",
                    bottom: -12,
                    left: "50%",
                    transform: "translateX(-50%)",
                    width: 4,
                    height: 4,
                    borderRadius: "50%",
                    backgroundColor: "var(--color-primary)",
                  }} />
                )}
              </button>
            );
          })}
        </nav>

        <div style={{ display: "flex", alignItems: "center", gap: 8, flexShrink: 0 }}>
          <span
            style={{
              display: "inline-block",
              width: 8,
              height: 8,
              borderRadius: "50%",
              backgroundColor: wsConnected ? "var(--color-success)" : "var(--color-error)",
              animation: wsConnected ? "heartbeat 2s ease-in-out infinite" : "none",
            }}
          />
          <span style={{ fontSize: 12, color: "var(--color-text-muted)" }}>
            {wsConnected ? "已连接" : "未连接"}
          </span>
        </div>
      </header>

      <main style={{ maxWidth: 800, margin: "0 auto", padding: "28px 16px", animation: "fade-in 0.35s ease" }}>
        {children}
      </main>
    </div>
  );
}
