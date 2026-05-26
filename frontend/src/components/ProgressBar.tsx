interface Props {
  progress: number;
}

export default function ProgressBar({ progress }: Props) {
  return (
    <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
      <div
        style={{
          flex: 1,
          height: 6,
          backgroundColor: "#f0f0f0",
          borderRadius: 3,
          overflow: "hidden",
        }}
      >
        <div
          style={{
            width: `${Math.min(progress, 100)}%`,
            height: "100%",
            backgroundColor: progress >= 100 ? "#52c41a" : "#1890ff",
            borderRadius: 3,
            transition: "width 0.3s ease",
          }}
        />
      </div>
      <span style={{ fontSize: 12, color: "#999", minWidth: 32, textAlign: "right" }}>
        {progress}%
      </span>
    </div>
  );
}
