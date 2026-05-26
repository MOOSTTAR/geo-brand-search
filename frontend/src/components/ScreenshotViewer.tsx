import { useState } from "react";

interface Props {
  url: string | null;
  onClose: () => void;
}

export default function ScreenshotViewer({ url, onClose }: Props) {
  const [zoom, setZoom] = useState(1);
  const [loading, setLoading] = useState(true);

  if (!url) return null;

  return (
    <div
      onClick={onClose}
      style={{
        position: "fixed",
        inset: 0,
        backgroundColor: "rgba(0,0,0,0.75)",
        zIndex: 1000,
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
      }}
    >
      {/* Toolbar */}
      <div
        style={{
          position: "absolute",
          top: 16,
          right: 16,
          display: "flex",
          gap: 8,
          zIndex: 1001,
        }}
      >
        <button
          onClick={(e) => { e.stopPropagation(); setZoom((z) => Math.min(5, z + 0.2)); }}
          style={toolbarBtnStyle}
        >
          +
        </button>
        <button
          onClick={(e) => { e.stopPropagation(); setZoom((z) => Math.max(0.2, z - 0.2)); }}
          style={toolbarBtnStyle}
        >
          -
        </button>
        <button
          onClick={(e) => { e.stopPropagation(); setZoom(1); }}
          style={toolbarBtnStyle}
        >
          {Math.round(zoom * 100)}%
        </button>
        <button onClick={onClose} style={{ ...toolbarBtnStyle, fontSize: 18 }}>
          ✕
        </button>
      </div>

      {/* Image container — fills available space, scrolls when zoomed */}
      <div
        onClick={(e) => e.stopPropagation()}
        style={{
          width: "92vw",
          height: "90vh",
          overflow: "auto",
        }}
      >
        {loading && (
          <div style={{ padding: 40, color: "#fff", textAlign: "center" }}>加载截图中...</div>
        )}
        <img
          src={url}
          alt="Screenshot"
          onLoad={() => setLoading(false)}
          style={{
            display: "block",
            width: `${zoom * 100}%`,
            minWidth: zoom === 1 ? "100%" : undefined,
            transition: "width 0.15s",
          }}
        />
      </div>
    </div>
  );
}

const toolbarBtnStyle: React.CSSProperties = {
  padding: "6px 14px",
  fontSize: 14,
  backgroundColor: "rgba(255,255,255,0.2)",
  color: "#fff",
  border: "1px solid rgba(255,255,255,0.3)",
  borderRadius: 4,
  cursor: "pointer",
};
