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


export const buildApiUrl = (url: string, language: Language | undefined) => {
  const lang = language === "en" ? "en" : "zh";
  const separator = url.includes("?") ? "&" : "?";
  return `${url}${separator}language=${encodeURIComponent(lang)}`;
};

export const getLanguageHeaders = (language: Language | undefined) => ({
  "Accept-Language": language === "en" ? "en" : "zh-CN",
  "X-Language": language === "en" ? "en" : "zh",
});
