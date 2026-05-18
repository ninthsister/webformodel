"use client";

import { useEffect, useMemo, useState } from "react";
import { FileSearchOutlined } from "@ant-design/icons";
import { Card, Space, Spin, Tag, Typography, message } from "antd";

const { Text } = Typography;

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

type EvidenceItem = {
  title: string;
  color: "orange" | "blue" | "gray" | "green" | "slate";
  status?: string;
  missing?: boolean;
  highlight?: boolean;
};

type KeyEvidenceResponse = {
  evidenceItems?: EvidenceItem[];
  summary?: string;
};

const DEFAULT_EVIDENCE_ITEMS: EvidenceItem[] = [
  {
    title: "MRI T2WI",
    color: "orange",
    status: "已提供",
    highlight: true,
  },
  {
    title: "MRI DWI",
    color: "blue",
    status: "已提供",
  },
  {
    title: "PET/CT 缺失",
    color: "gray",
    status: "缺失",
    missing: true,
  },
  {
    title: "CT 已提供",
    color: "green",
    status: "已提供",
  },
];

const DEFAULT_SUMMARY =
  "PET/CT 检查缺失。建议进一步进行代谢影像学评估，以判断可疑淋巴结状态。";

function getAnalysisStatus(patient?: Patient) {
  return patient?.analysisStatus || patient?.analysis?.status || "未分析";
}

function getBorderClassName(color: EvidenceItem["color"]) {
  if (color === "orange") return "border-orange-400";
  if (color === "blue") return "border-blue-400";
  if (color === "green") return "border-green-400";
  return "border-slate-300";
}

function getStatusTagColor(item: EvidenceItem) {
  if (item.missing) return "default";
  if (item.color === "orange") return "orange";
  if (item.color === "blue") return "blue";
  if (item.color === "green") return "green";
  return "default";
}

function EvidenceBlock({ item }: { item: EvidenceItem }) {
  return (
    <div className="text-center">
      <div
        className={`relative mb-2 h-24 rounded-lg border bg-slate-900 ${getBorderClassName(
          item.color
        )}`}
      >
        {item.missing ? (
          <div className="flex h-full items-center justify-center text-4xl font-bold text-slate-400">
            ?
          </div>
        ) : (
          <div className="absolute inset-0 bg-[radial-gradient(circle,rgba(160,160,160,0.55),rgba(20,20,20,0.95))]" />
        )}

        {item.highlight && (
          <div className="absolute left-1/2 top-1/2 h-5 w-5 -translate-x-1/2 -translate-y-1/2 rounded-full border-2 border-orange-400" />
        )}
      </div>

      <div className="space-y-1">
        <Text className="block text-xs">{item.title}</Text>

        {item.status && (
          <Tag color={getStatusTagColor(item)} className="m-0 text-[10px]">
            {item.status}
          </Tag>
        )}
      </div>
    </div>
  );
}

export default function KeyEvidence({
  currentPatient,
  embedded = false,
}: {
  currentPatient?: Patient;
  embedded?: boolean;
}) {
  const [evidenceItems, setEvidenceItems] =
    useState<EvidenceItem[]>(DEFAULT_EVIDENCE_ITEMS);
  const [summary, setSummary] = useState(DEFAULT_SUMMARY);
  const [loading, setLoading] = useState(false);

  const analysisStatus = useMemo(
    () => getAnalysisStatus(currentPatient),
    [currentPatient]
  );

  const isAnalysisFinished = analysisStatus === "completed";

  useEffect(() => {
    const patientId: string = currentPatient?.id as string;

    if (!patientId || patientId === "??????") {
      setEvidenceItems(DEFAULT_EVIDENCE_ITEMS);
      setSummary(DEFAULT_SUMMARY);
      return;
    }

    if (!isAnalysisFinished) {
      setEvidenceItems(DEFAULT_EVIDENCE_ITEMS);
      setSummary(DEFAULT_SUMMARY);
      return;
    }

    let ignore = false;

    async function fetchKeyEvidence() {
      try {
        setLoading(true);

        const res = await fetch(
          `http://127.0.0.1:8000/api/patient/${encodeURIComponent(
            patientId
          )}/key-evidence`
        );

        if (!res.ok) {
          throw new Error(`请求失败: ${res.status}`);
        }

        const data: KeyEvidenceResponse = await res.json();

        if (ignore) return;

        if (data.evidenceItems && data.evidenceItems.length > 0) {
          setEvidenceItems(data.evidenceItems);
        } else {
          setEvidenceItems(DEFAULT_EVIDENCE_ITEMS);
        }

        setSummary(data.summary || DEFAULT_SUMMARY);
      } catch (error) {
        if (!ignore) {
          console.error("获取关键证据失败:", error);
          message.warning("暂未获取到后端关键证据，已使用默认关键证据");
          setEvidenceItems(DEFAULT_EVIDENCE_ITEMS);
          setSummary(DEFAULT_SUMMARY);
        }
      } finally {
        if (!ignore) {
          setLoading(false);
        }
      }
    }

    fetchKeyEvidence();

    return () => {
      ignore = true;
    };
  }, [currentPatient?.id, isAnalysisFinished,currentPatient?.analysis?.started_at]);

  const content = (
    <Spin spinning={loading}>
      <div className="grid grid-cols-4 gap-3">
        {evidenceItems.map((item) => (
          <EvidenceBlock key={item.title} item={item} />
        ))}
      </div>

      <div className="mt-3 rounded bg-slate-50 p-2 text-xs text-slate-500">
        {summary}
      </div>
    </Spin>
  );

  if (embedded) {
    return content;
  }

  return (
    <Card
      title={
        <Space>
          <FileSearchOutlined className="text-blue-600" />
          <span>关键证据</span>
          <Tag color={isAnalysisFinished ? "green" : "default"}>
            {analysisStatus}
          </Tag>
        </Space>
      }
      className="h-full shadow-sm"
    >
      {content}
    </Card>
  );
}