import { useState, useCallback } from "react";
import { getScreenshotUrl } from "../api/types";

export function useScreenshot() {
  const [screenshotUrl, setScreenshotUrl] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const openScreenshot = useCallback((taskId: string) => {
    setLoading(true);
    setError(null);
    const url = getScreenshotUrl(taskId);
    setScreenshotUrl(url);
    setLoading(false);
  }, []);

  const closeScreenshot = useCallback(() => {
    setScreenshotUrl(null);
    setError(null);
  }, []);

  return { screenshotUrl, loading, error, openScreenshot, closeScreenshot };
}
