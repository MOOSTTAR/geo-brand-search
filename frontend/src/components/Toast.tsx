import { useEffect, useState } from "react";

export interface ToastItem {
  id: number;
  message: string;
  type: "success" | "error" | "info";
}

let _nextId = 0;
let _addToast: ((msg: string, type: ToastItem["type"]) => void) | null = null;

export function showToast(message: string, type: ToastItem["type"] = "info") {
  _addToast?.(message, type);
}

const COLORS: Record<ToastItem["type"], { bg: string; border: string; color: string }> = {
  success: { bg: "#f6ffed", border: "#b7eb8f", color: "#52c41a" },
  error: { bg: "#fff2f0", border: "#ffccc7", color: "#ff4d4f" },
  info: { bg: "#e6f4ff", border: "#91caff", color: "#1677ff" },
};

export default function ToastContainer() {
  const [toasts, setToasts] = useState<ToastItem[]>([]);

  useEffect(() => {
    _addToast = (message, type) => {
      const id = ++_nextId;
      setToasts((prev) => [...prev, { id, message, type }]);
      setTimeout(() => {
        setToasts((prev) => prev.filter((t) => t.id !== id));
      }, 2500);
    };
  }, []);

  if (toasts.length === 0) return null;

  return (
    <div style={{ position: "fixed", top: 20, right: 20, zIndex: 2000, display: "flex", flexDirection: "column", gap: 8 }}>
      {toasts.map((t) => {
        const c = COLORS[t.type];
        return (
          <div
            key={t.id}
            style={{
              padding: "10px 20px",
              backgroundColor: c.bg,
              border: `1px solid ${c.border}`,
              borderRadius: 6,
              color: c.color,
              fontSize: 14,
              fontWeight: 500,
              boxShadow: "0 4px 12px rgba(0,0,0,0.1)",
              animation: "toast-in 0.25s ease",
              maxWidth: 360,
            }}
          >
            {t.message}
          </div>
        );
      })}
    </div>
  );
}
