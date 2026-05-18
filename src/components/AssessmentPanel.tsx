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

const DEFAULT_ASSESSMENTS: AssessmentItem[] = [
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

function getAnalysisStatus(patient?: Patient) {
  return patient?.analysisStatus || patient?.analysis?.status || "未分析";
}

function AssessmentBlock({ item }: { item: AssessmentItem }) {
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
        <Text type="secondary">证据充分性</Text>
        <Text className={item.evidenceClassName}>
          {item.evidenceSufficiency}
        </Text>

        <Text type="secondary">模型一致性</Text>
        <Text>{item.modelConsistency}</Text>

        <Text type="secondary">阳性切片比例</Text>
        <Text>{item.positiveSliceRatio}</Text>

        <Text type="secondary">关键发现</Text>
        <Text>{item.keyFinding}</Text>
      </div>
    </div>
  );
}

export default function AssessmentPanel({
  currentPatient,
}: {
  currentPatient: Patient;
}) {
  const [assessments, setAssessments] =
    useState<AssessmentItem[]>(DEFAULT_ASSESSMENTS);
  const [loading, setLoading] = useState(false);

  const analysisStatus = useMemo(
    () => getAnalysisStatus(currentPatient),
    [currentPatient]
  );

  const isAnalysisFinished = analysisStatus === "completed";

  useEffect(() => {
    const patientId = currentPatient?.id;

    if (!patientId || patientId === "??????") {
      setAssessments(DEFAULT_ASSESSMENTS);
      return;
    }

    if (!isAnalysisFinished) {
      setAssessments(DEFAULT_ASSESSMENTS);
      return;
    }

    let ignore = false;

    async function fetchAssessment() {
      try {
        setLoading(true);

        const res = await fetch(
          `http://127.0.0.1:8000/api/patient/${encodeURIComponent(
            patientId
          )}/assessment`
        );

        if (!res.ok) {
          throw new Error(`请求失败: ${res.status}`);
        }

        const data: AssessmentResponse = await res.json();

        if (ignore) return;
        if (data.assessments && data.assessments.length > 0) {
          setAssessments(data.assessments);
        } else {
          setAssessments(DEFAULT_ASSESSMENTS);
        }
      } catch (error) {
        if (!ignore) {
          console.error("获取评估结果失败:", error);
          message.warning("暂未获取到后端评估结果，已使用默认评估信息");
          setAssessments(DEFAULT_ASSESSMENTS);
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
  }, [currentPatient?.id, isAnalysisFinished,currentPatient?.analysis?.started_at]);

  return (
    <Card
      title={
        <Space>
          <AlertOutlined className="text-blue-600" />
          <span>评估</span>
          <Tag color={isAnalysisFinished ? "green" : "default"}>
            {analysisStatus}
          </Tag>
        </Space>
      }
      className="h-full shadow-sm"
    >
      <Spin spinning={loading}>
        <div className="space-y-4">
          {assessments.map((item, index) => (
            <div key={item.title}>
              <AssessmentBlock item={item} />
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