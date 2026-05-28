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
    <div style={{ minHeight: "100vh", backgroundColor: "#fafafa" }}>
      <header
        style={{
          padding: "0 24px",
          height: 52,
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          backgroundColor: "#fff",
          borderBottom: "1px solid #f0f0f0",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: 24 }}>
          <h1 style={{ fontSize: 18, fontWeight: 600, margin: 0, color: "#333", whiteSpace: "nowrap" }}>
            GEO 品牌查询
          </h1>

          {/* Tab navigation */}
          <nav style={{ display: "flex", gap: 0, height: 52 }}>
            {TABS.map((tab) => {
              const isActive = activeTab === tab.key;
              return (
                <button
                  key={tab.key}
                  onClick={() => onTabChange(tab.key)}
                  style={{
                    padding: "0 20px",
                    height: 52,
                    fontSize: 14,
                    fontWeight: isActive ? 600 : 400,
                    color: isActive ? "#1890ff" : "#666",
                    backgroundColor: "transparent",
                    border: "none",
                    borderBottom: isActive ? "2px solid #1890ff" : "2px solid transparent",
                    cursor: "pointer",
                    transition: "all 0.2s",
                    whiteSpace: "nowrap",
                  }}
                >
                  {tab.label}
                </button>
              );
            })}
          </nav>
        </div>

        <div style={{ display: "flex", alignItems: "center", gap: 8, flexShrink: 0 }}>
          <span
            style={{
              display: "inline-block",
              width: 8,
              height: 8,
              borderRadius: "50%",
              backgroundColor: wsConnected ? "#52c41a" : "#ff4d4f",
            }}
          />
          <span style={{ fontSize: 12, color: "#999" }}>
            {wsConnected ? "已连接" : "未连接"}
          </span>
        </div>
      </header>

      <main style={{ maxWidth: 800, margin: "0 auto", padding: "24px 16px" }}>
        {children}
      </main>
    </div>
  );
}
