"use client";

import { useEffect, useMemo, useState } from "react";
import { AlertOutlined } from "@ant-design/icons";
import {
  Card,
  Divider,
  Progress,
  Space,
  Spin,
  Tag,
  Typography,
  message,
} from "antd";
import type { Language } from "@/components/i18n";
import { buildApiUrl, getLanguageHeaders, statusText, zhEn } from "@/components/i18n";

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

type AssessmentItem = {
  title: string;
  riskText: string;
  riskColor?: string;
  percent: number;
  strokeColor: string;
  railColor: string;
  borderClassName: string;
  bgClassName: string;
  evidenceSufficiency: string;
  evidenceClassName?: string;
  modelConsistency: string;
  positiveSliceRatio: string;
  keyFinding: string;
};

type AssessmentResponse = {
  assessments?: AssessmentItem[];
};

const DEFAULT_ASSESSMENTS_ZH: AssessmentItem[] = [
  {
    title: "盆腔淋巴结转移",
    riskText: "中等风险",
    riskColor: "orange",
    percent: 58.3,
    strokeColor: "#f59e0b",
    railColor: "#fde7c7",
    borderClassName: "border-orange-200",
    bgClassName: "bg-orange-50",
    evidenceSufficiency: "不足",
    evidenceClassName: "text-red-500",
    modelConsistency: "中等",
    positiveSliceRatio: "47 / 429",
    keyFinding: "左侧髂外淋巴结可疑",
  },
  {
    title: "宫旁浸润",
    riskText: "不确定",
    riskColor: "default",
    percent: 31.2,
    strokeColor: "#64748b",
    railColor: "#e2e8f0",
    borderClassName: "border-slate-200",
    bgClassName: "bg-slate-50",
    evidenceSufficiency: "不足",
    evidenceClassName: "text-red-500",
    modelConsistency: "低",
    positiveSliceRatio: "1 / 6",
    keyFinding: "宫旁界面显示不清",
  },
];

const DEFAULT_ASSESSMENTS_EN: AssessmentItem[] = [
  {
    title: "Pelvic lymph node metastasis",
    riskText: "Moderate risk",
    riskColor: "orange",
    percent: 58.3,
    strokeColor: "#f59e0b",
    railColor: "#fde7c7",
    borderClassName: "border-orange-200",
    bgClassName: "bg-orange-50",
    evidenceSufficiency: "Insufficient",
    evidenceClassName: "text-red-500",
    modelConsistency: "Moderate",
    positiveSliceRatio: "47 / 429",
    keyFinding: "Suspicious left external iliac lymph node",
  },
  {
    title: "Parametrial invasion",
    riskText: "Uncertain",
    riskColor: "default",
    percent: 31.2,
    strokeColor: "#64748b",
    railColor: "#e2e8f0",
    borderClassName: "border-slate-200",
    bgClassName: "bg-slate-50",
    evidenceSufficiency: "Insufficient",
    evidenceClassName: "text-red-500",
    modelConsistency: "Low",
    positiveSliceRatio: "1 / 6",
    keyFinding: "Parametrial interface is unclear",
  },
];

function getDefaultAssessments(language?: Language) {
  return language === "en" ? DEFAULT_ASSESSMENTS_EN : DEFAULT_ASSESSMENTS_ZH;
}

function getAnalysisStatus(patient?: Patient) {
  return patient?.analysisStatus || patient?.analysis?.status || "未分析";
}

function AssessmentBlock({ item, language }: { item: AssessmentItem; language?: Language }) {
  return (
    <div
      className={`rounded-lg border p-3 ${item.borderClassName} ${item.bgClassName}`}
    >
      <div className="mb-2 flex items-center justify-between">
        <Text strong>{item.title}</Text>
        <Tag color={item.riskColor}>{item.riskText}</Tag>
      </div>

      <Progress
        percent={item.percent}
        strokeColor={item.strokeColor}
        railColor={item.railColor}
        format={(percent) => `${percent}%`}
      />

      <div className="mt-3 grid grid-cols-2 gap-2 text-xs">
        <Text type="secondary">{zhEn(language, "证据充分性", "Evidence sufficiency")}</Text>
        <Text className={item.evidenceClassName}>
          {item.evidenceSufficiency}
        </Text>

        <Text type="secondary">{zhEn(language, "模型一致性", "Model consistency")}</Text>
        <Text>{item.modelConsistency}</Text>

        <Text type="secondary">{zhEn(language, "阳性切片比例", "Positive slice ratio")}</Text>
        <Text>{item.positiveSliceRatio}</Text>

        <Text type="secondary">{zhEn(language, "关键发现", "Key finding")}</Text>
        <Text>{item.keyFinding}</Text>
      </div>
    </div>
  );
}

export default function AssessmentPanel({
  currentPatient,
  language = "zh",
}: {
  currentPatient: Patient;
  language?: Language;
}) {
  const [assessments, setAssessments] =
    useState<AssessmentItem[]>(getDefaultAssessments(language));
  const [loading, setLoading] = useState(false);

  const analysisStatus = useMemo(
    () => getAnalysisStatus(currentPatient),
    [currentPatient]
  );

  const isAnalysisFinished = analysisStatus === "completed";

  useEffect(() => {
    const patientId = currentPatient?.id;

    if (!patientId || patientId === "??????") {
      setAssessments(getDefaultAssessments(language));
      return;
    }

    if (!isAnalysisFinished) {
      setAssessments(getDefaultAssessments(language));
      return;
    }

    let ignore = false;

    async function fetchAssessment() {
      try {
        setLoading(true);

        const res = await fetch(
          buildApiUrl(
            `/api/patient/${encodeURIComponent(
              patientId
            )}/assessment`,
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

        const data: AssessmentResponse = await res.json();

        if (ignore) return;
        if (data.assessments && data.assessments.length > 0) {
          setAssessments(data.assessments);
        } else {
          setAssessments(getDefaultAssessments(language));
        }
      } catch (error) {
        if (!ignore) {
          console.error("获取评估结果失败:", error);
          message.warning(zhEn(language, "暂未获取到后端评估结果，已使用默认评估信息", "Backend assessment is unavailable. Default assessment is shown."));
          setAssessments(getDefaultAssessments(language));
        }
      } finally {
        if (!ignore) {
          setLoading(false);
        }
      }
    }

    fetchAssessment();

    return () => {
      ignore = true;
    };
  }, [currentPatient?.id, isAnalysisFinished, currentPatient?.analysis?.started_at, language]);

  return (
    <Card
      title={
        <Space>
          <AlertOutlined className="text-blue-600" />
          <span>{zhEn(language, "评估", "Assessment")}</span>
          <Tag color={isAnalysisFinished ? "green" : "default"}>
            {statusText(language, analysisStatus)}
          </Tag>
        </Space>
      }
      className="h-full shadow-sm"
    >
      <Spin spinning={loading}>
        <div className="space-y-4">
          {assessments.map((item, index) => (
            <div key={item.title}>
              <AssessmentBlock item={item} language={language} />
              {index !== assessments.length - 1 && (
                <Divider className="my-4" />
              )}
            </div>
          ))}
        </div>
      </Spin>
    </Card>
  );
}