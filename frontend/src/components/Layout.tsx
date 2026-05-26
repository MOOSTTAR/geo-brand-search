import type { ReactNode } from "react";

interface Props {
  wsConnected: boolean;
  children: ReactNode;
}

export default function Layout({ wsConnected, children }: Props) {
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
        <h1 style={{ fontSize: 18, fontWeight: 600, margin: 0, color: "#333" }}>
          GEO 品牌查询
        </h1>
        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
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
