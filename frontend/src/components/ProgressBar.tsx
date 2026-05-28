interface Props {
  progress: number;
}

export default function ProgressBar({ progress }: Props) {
  const done = progress >= 100;

  return (
    <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
      <div
        style={{
          flex: 1,
          height: 6,
          backgroundColor: "var(--color-border)",
          borderRadius: 3,
          overflow: "hidden",
        }}
      >
        <div
          style={{
            width: `${Math.min(progress, 100)}%`,
            height: "100%",
            borderRadius: 3,
            transition: "width 0.5s cubic-bezier(0.4, 0, 0.2, 1)",
            background: done
              ? "var(--color-success)"
              : "var(--color-primary-gradient)",
            backgroundSize: done ? undefined : "200% 100%",
            animation: done ? undefined : "shimmer 2s linear infinite",
            position: "relative",
          }}
        />
      </div>
      <span style={{
        fontSize: 12,
        fontWeight: 600,
        color: done ? "var(--color-success)" : "var(--color-primary)",
        minWidth: 34,
        textAlign: "right",
        transition: "color var(--transition)",
      }}>
        {progress}%
      </span>
    </div>
  );
}
