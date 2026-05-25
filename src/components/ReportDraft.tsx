"use client";

import { useEffect, useMemo, useState } from "react";
import { FileTextOutlined } from "@ant-design/icons";
import { Card, Space, Typography, Spin, message, Tag } from "antd";
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
  language?: Language;
};

const DEFAULT_REPORT_SECTIONS_ZH: ReportSection[] = [
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

const DEFAULT_REPORT_SECTIONS_EN: ReportSection[] = [
  { title: "Pelvic lymph node assessment:", content: "The current patient has not completed automatic analysis. The system is temporarily displaying a default report draft. After analysis is completed, the AI report draft will be loaded from the backend.", titleClassName: "text-red-500" },
  { title: "Parametrial invasion assessment:", content: "The current analysis has not been completed, so a clear assessment based on MRI, DWI, or contrast-enhanced imaging cannot be provided yet.", titleClassName: "text-green-600" },
  { title: "Final recommendation:", content: "Please import patient images and basic information first, then click Start Analysis. After analysis is completed, the AI report draft will be updated automatically.", titleClassName: "text-blue-600" },
];

function getDefaultReportSections(language?: Language) {
  return language === "en" ? DEFAULT_REPORT_SECTIONS_EN : DEFAULT_REPORT_SECTIONS_ZH;
}

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
  language = "zh",
}: ReportDraftProps) {
  const [reportSections, setReportSections] = useState<ReportSection[]>(
    getDefaultReportSections(language)
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
      setReportSections(getDefaultReportSections(language));
      setLoading(false);
      return;
    }

    if (!isAnalysisFinished) {
      setReportSections(getDefaultReportSections(language));
      setLoading(false);
      return;
    }

    let ignore = false;

    async function fetchReportDraft() {
      try {
        setLoading(true);

        const res = await fetch(
          buildApiUrl(
            `http://127.0.0.1:8000/api/patient/AIreport/${encodeURIComponent(
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
          : getDefaultReportSections(language);

        if (nextSections.length > 0) {
          setReportSections(nextSections);
        } else {
          setReportSections(getDefaultReportSections(language));
        }
      } catch (error) {
        if (!ignore) {
          console.error("获取 AI 报告草稿失败:", error);
          message.warning(zhEn(language, "暂未获取到后端 AI 报告草稿，已使用默认报告内容", "Backend AI report draft is unavailable. Default report content is shown."));
          setReportSections(getDefaultReportSections(language));
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
  }, [currentPatient?.id, isAnalysisFinished, currentPatient?.analysis?.started_at, language]);

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
          <span>{zhEn(language, "AI 生成报告草稿", "AI-generated Report Draft")}</span>
          <Tag color={isAnalysisFinished ? "green" : "default"}>
            {statusText(language, analysisStatus)}
          </Tag>
        </Space>
      }
      className="h-full shadow-sm"
    >
      {content}
    </Card>
  );
}