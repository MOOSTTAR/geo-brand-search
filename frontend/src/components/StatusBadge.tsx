interface Props {
  status: string;
}

const STATUS_CONFIG: Record<string, { label: string; bg: string; text: string; dot: string }> = {
  creating: { label: "排队中", bg: "#f3f4f6", text: "#6b7280", dot: "#9ca3af" },
  executing: { label: "执行中", bg: "#eeedff", text: "#5b5ef7", dot: "#5b5ef7" },
  completed: { label: "已完成", bg: "#ecfdf5", text: "#10b981", dot: "#10b981" },
  failed: { label: "失败", bg: "#fef2f2", text: "#ef4444", dot: "#ef4444" },
};

export default function StatusBadge({ status }: Props) {
  const config = STATUS_CONFIG[status] ?? { label: status, bg: "#f3f4f6", text: "#6b7280", dot: "#9ca3af" };
  const isExecuting = status === "executing";

  return (
    <span
      style={{
        display: "inline-flex",
        alignItems: "center",
        gap: 6,
        padding: "3px 12px",
        borderRadius: 20,
        fontSize: 12,
        fontWeight: 600,
        backgroundColor: config.bg,
        color: config.text,
        transition: "all var(--transition)",
      }}
    >
      <span
        style={{
          display: "inline-block",
          width: 7,
          height: 7,
          borderRadius: "50%",
          backgroundColor: config.dot,
          animation: isExecuting ? "heartbeat 1.2s ease-in-out infinite" : "none",
        }}
      />
      {config.label}
    </span>
  );
}
