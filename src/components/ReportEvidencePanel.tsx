"use client";
import { useEffect, useMemo, useState } from "react";
import { FileTextOutlined } from "@ant-design/icons";
import { Card, Space, Tag } from "antd";
import ReportDraft from "@/components/ReportDraft";
import KeyEvidence from "@/components/KeyEvidence";
import type { Language } from "@/components/i18n";
import { statusText, zhEn } from "@/components/i18n";
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
  };
};
function getAnalysisStatus(patient?: Patient) {
  return patient?.analysisStatus || patient?.analysis?.status || "未分析";
}
export default function ReportEvidencePanel({ currentPatient, language = "zh" }: { currentPatient: Patient; language?: Language }) {
  const analysisStatus = useMemo(
      () => getAnalysisStatus(currentPatient),
      [currentPatient]
    );
  const isAnalysisFinished = analysisStatus === "completed";
  return (
    <Card
      className="h-full shadow-sm"
      title={
        <div className="grid grid-cols-[1fr_420px]">
          <div className="px-6">
            <Space>
              <FileTextOutlined />
              <span>{zhEn(language, "AI 生成报告草稿", "AI-generated Report Draft")}</span>
              <Tag color={isAnalysisFinished ? "green" : "default"}>
                {statusText(language, analysisStatus)}
              </Tag>
            </Space>
          </div>

          <div className="border-l border-slate-200 px-6">
            <Space>
              <span>{zhEn(language, "关键证据", "Key Evidence")}</span>
              <Tag color={isAnalysisFinished ? "green" : "default"}>
                {statusText(language, analysisStatus)}
              </Tag>
            </Space>
          </div>
        </div>
      }
    >
      <div className="relative grid h-full grid-cols-[1fr_420px]">
        <div className="absolute bottom-4 left-[calc(100%-420px)] top-4 w-px scale-x-50 origin-center bg-slate-200" />

        <div className="p-6">
          <ReportDraft embedded currentPatient={currentPatient} language={language} />
        </div>

        <div className="p-6">
          <KeyEvidence embedded currentPatient={currentPatient} language={language} />
        </div>
      </div>
    </Card>
  );
}