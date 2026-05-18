"use client";

import { useEffect, useMemo, useState } from "react";
import { FileTextOutlined } from "@ant-design/icons";
import { Card, Space, Typography, Spin, message, Tag } from "antd";

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

type ReportSection = {
  title: string;
  content: string;
  titleClassName?: string;
};

type ReportResponse = {
  patient_id?: string;

  /**
   * 对齐你的后端返回：
   * {
   *   patient_id: "...",
   *   aireportdraft: [...]
   * }
   */
  aireportdraft?: ReportSection[];

  /**
   * 可选兼容字段：
   * 如果你以后后端改成 reportSections，也不会报错
   */
  reportSections?: ReportSection[];
};

type ReportDraftProps = {
  embedded?: boolean;
  currentPatient?: Patient;
};

const DEFAULT_REPORT_SECTIONS: ReportSection[] = [
  {
    title: "盆腔淋巴结评估：",
    content:
      "当前病人尚未完成自动分析，系统暂时使用默认报告草稿进行展示。待分析完成后，将自动从后端读取 AI 报告草稿。",
    titleClassName: "text-red-500",
  },
  {
    title: "宫旁浸润评估：",
    content:
      "当前分析尚未完成，暂不能根据 MRI、DWI 或增强影像给出明确宫旁浸润判断。",
    titleClassName: "text-green-600",
  },
  {
    title: "最终建议：",
    content:
      "请先导入病人影像和基础信息，并点击开始分析。分析完成后，系统会自动更新 AI 报告草稿。",
    titleClassName: "text-blue-600",
  },
];

function getAnalysisStatus(patient?: Patient) {
  return patient?.analysisStatus || patient?.analysis?.status || "未分析";
}

function ReportContent({ sections }: { sections: ReportSection[] }) {
  return (
    <div className="rounded-lg bg-slate-50 p-4 text-sm leading-6">
      {sections.map((section, index) => (
        <div key={`${section.title}-${index}`}>
          <Text strong className={section.titleClassName || "text-blue-600"}>
            {section.title}
          </Text>

          <Paragraph
            className={
              index === sections.length - 1 ? "!mb-0 !mt-1" : "!mb-2 !mt-1"
            }
          >
            {section.content}
          </Paragraph>
        </div>
      ))}
    </div>
  );
}

export default function ReportDraft({
  embedded = false,
  currentPatient,
}: ReportDraftProps) {
  const [reportSections, setReportSections] = useState<ReportSection[]>(
    DEFAULT_REPORT_SECTIONS
  );
  const [loading, setLoading] = useState(false);

  const analysisStatus = useMemo(
    () => getAnalysisStatus(currentPatient),
    [currentPatient]
  );

  const isAnalysisFinished = analysisStatus === "completed";

  useEffect(() => {
    // 申明一下patientId是string
    const patientId: string = currentPatient?.id as string;

    if (!patientId || patientId === "??????") {
      setReportSections(DEFAULT_REPORT_SECTIONS);
      setLoading(false);
      return;
    }

    if (!isAnalysisFinished) {
      setReportSections(DEFAULT_REPORT_SECTIONS);
      setLoading(false);
      return;
    }

    let ignore = false;

    async function fetchReportDraft() {
      try {
        setLoading(true);

        const res = await fetch(
          `http://127.0.0.1:8000/api/patient/AIreport/${encodeURIComponent(
            patientId
          )}`,
          {
            method: "GET",
          }
        );

        if (!res.ok) {
          throw new Error(`请求失败: ${res.status}`);
        }

        const data: ReportResponse | ReportSection[] = await res.json();

        if (ignore) return;

        /**
         * 兼容三种后端格式：
         *
         * 1. 当前你的后端：
         * {
         *   patient_id: "C-2026-0128",
         *   aireportdraft: [
         *     { title: "...", content: "...", titleClassName: "..." }
         *   ]
         * }
         *
         * 2. 兼容旧字段：
         * {
         *   patient_id: "C-2026-0128",
         *   reportSections: [...]
         * }
         *
         * 3. 直接返回数组：
         * [
         *   { title: "...", content: "..." }
         * ]
         */
        const nextSections = Array.isArray(data)
          ? data
          : Array.isArray(data.aireportdraft)
          ? data.aireportdraft
          : Array.isArray(data.reportSections)
          ? data.reportSections
          : DEFAULT_REPORT_SECTIONS;

        if (nextSections.length > 0) {
          setReportSections(nextSections);
        } else {
          setReportSections(DEFAULT_REPORT_SECTIONS);
        }
      } catch (error) {
        if (!ignore) {
          console.error("获取 AI 报告草稿失败:", error);
          message.warning("暂未获取到后端 AI 报告草稿，已使用默认报告内容");
          setReportSections(DEFAULT_REPORT_SECTIONS);
        }
      } finally {
        if (!ignore) {
          setLoading(false);
        }
      }
    }

    fetchReportDraft();

    return () => {
      ignore = true;
    };
  }, [currentPatient?.id, isAnalysisFinished,currentPatient?.analysis?.started_at]);

  const content = (
    <Spin spinning={loading}>
      <ReportContent sections={reportSections} />
    </Spin>
  );

  if (embedded) {
    return content;
  }

  return (
    <Card
      title={
        <Space>
          <FileTextOutlined className="text-blue-600" />
          <span>AI 生成报告草稿</span>
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