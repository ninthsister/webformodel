"use client";

import { useEffect, useMemo, useState } from "react";
import { InfoCircleOutlined, WarningFilled } from "@ant-design/icons";
import { Card, Space, Typography, Spin, Tag, message } from "antd";
import type { Language } from "@/components/i18n";
import { buildApiUrl, getLanguageHeaders, statusText, zhEn } from "@/components/i18n";

const { Text, Paragraph } = Typography;

type Patient = {
  id: string;
  name?: string;
  age?: number;
  sex?: string;
  gender?: string;
  stage?: string;
  date?: string;
  modalities?: string[];
  analysisStatus?: string;
  analysis?: {
    status?: string;
    started_at?: string | null;
  };
};

type EvidenceSubItem = {
  name: string;
  status: string;
  className?: string;
};

type ReasoningItem = {
  type: "summary" | "conclusion" | "evidence" | "warning" | "suggestions";
  title: string;
  content?: string;
  className?: string;
  items?: EvidenceSubItem[] | string[];
};

type ReasoningResponse = {
  patient_id?: string;
  reasoning?: ReasoningItem[];
  reasoningItems?: ReasoningItem[];
};

const DEFAULT_REASONING_ITEMS_ZH: ReasoningItem[] = [
  {
    type: "summary",
    title: "推理摘要",
    content:
      "当前病人尚未完成自动分析，系统暂时使用默认推理信息进行展示。待分析完成后，将自动从后端读取完整推理结果。",
    className: "text-blue-700",
  },
  {
    type: "conclusion",
    title: "评估结论",
    content: "当前分析尚未完成，暂不能给出明确的术前评估结论。",
    className: "text-orange-600",
  },
  {
    type: "evidence",
    title: "证据充分性检查",
    items: [
      {
        name: "MRI",
        status: "等待分析",
        className: "text-orange-500",
      },
      {
        name: "PET/CT",
        status: "等待分析",
        className: "text-orange-500",
      },
      {
        name: "CT",
        status: "等待分析",
        className: "text-orange-500",
      },
      {
        name: "临床病史",
        status: "等待分析",
        className: "text-orange-500",
      },
    ],
  },
  {
    type: "warning",
    title: "风险提示",
    content: "自动分析尚未完成，当前内容为默认占位信息。",
    className: "text-red-600",
  },
  {
    type: "suggestions",
    title: "下一步建议",
    items: [
      "请先导入病人影像和基础信息",
      "点击开始分析按钮，等待模型完成推理",
      "分析完成后系统会自动更新证据状态和推理摘要",
    ],
  },
];

const DEFAULT_REASONING_ITEMS_EN: ReasoningItem[] = [
  { type: "summary", title: "Reasoning Summary", content: "The current patient has not completed automatic analysis. The system is temporarily displaying default reasoning information. After analysis is completed, full reasoning results will be loaded from the backend.", className: "text-blue-700" },
  { type: "conclusion", title: "Assessment Conclusion", content: "The current analysis has not been completed, so a clear preoperative assessment conclusion cannot be provided yet.", className: "text-orange-600" },
  { type: "evidence", title: "Evidence Sufficiency Check", items: [
    { name: "MRI", status: "Waiting for analysis", className: "text-orange-500" },
    { name: "PET/CT", status: "Waiting for analysis", className: "text-orange-500" },
    { name: "CT", status: "Waiting for analysis", className: "text-orange-500" },
    { name: "Clinical history", status: "Waiting for analysis", className: "text-orange-500" },
  ] },
  { type: "warning", title: "Risk Warning", content: "Automatic analysis has not been completed. The current content is default placeholder information.", className: "text-red-600" },
  { type: "suggestions", title: "Next Steps", items: [
    "Import patient images and basic information first",
    "Click Start Analysis and wait for model inference to finish",
    "After analysis is completed, the system will update evidence status and reasoning summary automatically",
  ] },
];

function getDefaultReasoningItems(language?: Language) {
  return language === "en" ? DEFAULT_REASONING_ITEMS_EN : DEFAULT_REASONING_ITEMS_ZH;
}

function getAnalysisStatus(patient?: Patient) {
  return patient?.analysisStatus || patient?.analysis?.status || "未分析";
}

function ReasoningBlock({ item }: { item: ReasoningItem }) {
  if (item.type === "summary") {
    return (
      <div className="rounded-lg border border-blue-200 bg-blue-50 p-3">
        <Text strong className={item.className || "text-blue-700"}>
          {item.title}
        </Text>

        <Paragraph className="!mb-0 !mt-2 text-xs">
          {item.content}
        </Paragraph>
      </div>
    );
  }

  if (item.type === "conclusion") {
    return (
      <div className="rounded-lg border border-red-200 bg-red-50 p-3">
        <Text strong className={item.className || "text-red-600"}>
          {item.content}
        </Text>
      </div>
    );
  }

  if (item.type === "evidence") {
    const evidenceItems = Array.isArray(item.items)
      ? (item.items as EvidenceSubItem[])
      : [];

    return (
      <div className="rounded-lg border border-slate-200 p-3">
        <Text strong>{item.title}</Text>

        <div className="mt-3 space-y-2 text-xs">
          {evidenceItems.map((evidence) => (
            <div key={evidence.name} className="flex justify-between">
              <span>{evidence.name}</span>
              <span className={evidence.className || "text-slate-500"}>
                {evidence.status}
              </span>
            </div>
          ))}
        </div>
      </div>
    );
  }

  if (item.type === "warning") {
    return (
      <div className="rounded border border-red-300 bg-red-50 p-2 text-xs">
        <span className={item.className || "text-red-600"}>
          <WarningFilled /> {item.content}
        </span>
      </div>
    );
  }

  if (item.type === "suggestions") {
    const suggestions = Array.isArray(item.items)
      ? (item.items as string[])
      : [];

    return (
      <div className="rounded-lg border border-blue-200 bg-blue-50 p-3">
        <Text strong className="text-blue-700">
          {item.title}
        </Text>

        <ol className="mt-2 space-y-1 pl-4 text-xs">
          {suggestions.map((suggestion, index) => (
            <li key={`${suggestion}-${index}`}>{suggestion}</li>
          ))}
        </ol>
      </div>
    );
  }

  return null;
}

export default function ReasoningPanel({
  currentPatient,
  language = "zh",
}: {
  currentPatient: Patient;
  language?: Language;
}) {
  const [reasoningItems, setReasoningItems] = useState<ReasoningItem[]>(
    getDefaultReasoningItems(language)
  );
  const [loading, setLoading] = useState(false);

  const analysisStatus = useMemo(
    () => getAnalysisStatus(currentPatient),
    [currentPatient]
  );

  const isAnalysisFinished = analysisStatus === "completed";

  useEffect(() => {
    const patientId = currentPatient?.id;

    if (!patientId || patientId === "??????") {
      setReasoningItems(getDefaultReasoningItems(language));
      return;
    }

    if (!isAnalysisFinished) {
      setReasoningItems(getDefaultReasoningItems(language));
      return;
    }

    let ignore = false;

    async function fetchReasoningItems() {
      try {
        setLoading(true);

        const res = await fetch(
          buildApiUrl(
            `http://127.0.0.1:8000/api/patient/reasoning/${encodeURIComponent(
              patientId
            )}`,
            language
          ),
          {
            method: "GET",
            headers: getLanguageHeaders(language),
          }
        );

        if (!res.ok) {
          throw new Error(`${zhEn(language, "请求失败", "Request failed")}: ${res.status}`);
        }

        const data: ReasoningResponse | ReasoningItem[] = await res.json();

        if (ignore) return;

        /**
         * 兼容三种后端格式：
         *
         * 1. 当前你的后端：
         * {
         *   patient_id: "...",
         *   reasoning: [...]
         * }
         *
         * 2. 之前建议的格式：
         * {
         *   patient_id: "...",
         *   reasoningItems: [...]
         * }
         *
         * 3. 直接返回数组：
         * [
         *   { type: "summary", ... }
         * ]
         */
        const nextItems = Array.isArray(data)
          ? data
          : Array.isArray(data.reasoning)
          ? data.reasoning
          : Array.isArray(data.reasoningItems)
          ? data.reasoningItems
          : getDefaultReasoningItems(language);

        if (nextItems.length > 0) {
          setReasoningItems(nextItems);
        } else {
          setReasoningItems(getDefaultReasoningItems(language));
        }
      } catch (error) {
        if (!ignore) {
          console.error("获取推理信息失败:", error);
          message.warning(zhEn(language, "暂未获取到后端推理结果，已使用默认推理信息", "Backend reasoning result is unavailable. Default reasoning is shown."));
          setReasoningItems(getDefaultReasoningItems(language));
        }
      } finally {
        if (!ignore) {
          setLoading(false);
        }
      }
    }

    fetchReasoningItems();

    return () => {
      ignore = true;
    };
  }, [currentPatient?.id, isAnalysisFinished, currentPatient?.analysis?.started_at, language]);

  return (
    <Card
      title={
        <Space>
          <InfoCircleOutlined className="text-blue-600" />
          <span>{zhEn(language, "证据状态", "Evidence Status")}</span>
          <Tag color={isAnalysisFinished ? "green" : "default"}>
            {statusText(language, analysisStatus)}
          </Tag>
        </Space>
      }
      className="h-full shadow-sm"
    >
      <Spin spinning={loading}>
        <div className="space-y-3">
          {reasoningItems.map((item, index) => (
            <ReasoningBlock key={`${item.type}-${index}`} item={item} />
          ))}
        </div>
      </Spin>
    </Card>
  );
}