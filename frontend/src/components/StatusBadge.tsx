interface Props {
  status: string;
}

const STATUS_CONFIG: Record<string, { label: string; bg: string; text: string }> = {
  creating: { label: "排队中", bg: "#f0f0f0", text: "#666" },
  executing: { label: "执行中", bg: "#e6f4ff", text: "#1890ff" },
  completed: { label: "已完成", bg: "#f6ffed", text: "#52c41a" },
  failed: { label: "失败", bg: "#fff2f0", text: "#ff4d4f" },
};

export default function StatusBadge({ status }: Props) {
  const config = STATUS_CONFIG[status] ?? { label: status, bg: "#f0f0f0", text: "#666" };

  return (
    <span
      style={{
        display: "inline-block",
        padding: "2px 10px",
        borderRadius: 4,
        fontSize: 12,
        fontWeight: 500,
        backgroundColor: config.bg,
        color: config.text,
      }}
    >
      {config.label}
    </span>
  );
}
