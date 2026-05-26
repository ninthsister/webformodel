export type Language = "zh" | "en";

export const zhEn = (language: Language | undefined, zh: string, en: string) =>
  language === "en" ? en : zh;

export const statusText = (language: Language | undefined, status?: string) => {
  if (language !== "en") return status || "未分析";
  const map: Record<string, string> = {
    not_started: "Not started",
    analyzing: "Analyzing",
    completed: "Completed",
    failed: "Failed",
    未分析: "Not analyzed",
    正在分析: "Analyzing",
    分析完成: "Completed",
    分析失败: "Failed",
    尚未开始分析: "Analysis not started",
  };
  return map[status || ""] || status || "Not analyzed";
};


export const API_BASE_URL = (
  process.env.NEXT_PUBLIC_API_BASE_URL || "http://127.0.0.1:8000"
).replace(/\/$/, "");

export const buildBackendUrl = (path: string) => {
  if (/^https?:\/\//i.test(path)) {
    return path.replace(/^https?:\/\/127\.0\.0\.1:8000/i, API_BASE_URL);
  }

  const normalizedPath = path.startsWith("/") ? path : `/${path}`;
  return `${API_BASE_URL}${normalizedPath}`;
};

export const buildApiUrl = (url: string, language: Language | undefined) => {
  const lang = language === "en" ? "en" : "zh";
  const realUrl = buildBackendUrl(url);
  const separator = realUrl.includes("?") ? "&" : "?";
  return `${realUrl}${separator}language=${encodeURIComponent(lang)}`;
};

export const getLanguageHeaders = (language: Language | undefined) => ({
  "Accept-Language": language === "en" ? "en" : "zh-CN",
  "X-Language": language === "en" ? "en" : "zh",
});
