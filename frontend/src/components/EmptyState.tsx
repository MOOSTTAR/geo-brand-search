export default function EmptyState() {
  return (
    <div
      style={{
        textAlign: "center",
        padding: "60px 20px",
        color: "#999",
      }}
    >
      <div style={{ fontSize: 48, marginBottom: 16, opacity: 0.3 }}>🔍</div>
      <div style={{ fontSize: 16, marginBottom: 8 }}>暂无任务</div>
      <div style={{ fontSize: 13 }}>在上方输入问题，开始一次搜索任务</div>
    </div>
  );
}
