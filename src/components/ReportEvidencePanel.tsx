"use client";

import { FileTextOutlined } from "@ant-design/icons";
import { Card, Space } from "antd";
import ReportDraft from "@/components/ReportDraft";
import KeyEvidence from "@/components/KeyEvidence";
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
export default function ReportEvidencePanel({ currentPatient }: { currentPatient: Patient }) {
  return (
    <Card
      className="h-full shadow-sm"
      title={
        <div className="grid grid-cols-[1fr_420px]">
          <div className="px-6">
            <Space>
              <FileTextOutlined />
              <span>AI 生成报告草稿</span>
            </Space>
          </div>

          <div className="border-l border-slate-200 px-6">关键证据</div>
        </div>
      }
    >
      <div className="relative grid h-full grid-cols-[1fr_420px]">
        <div className="absolute bottom-4 left-[calc(100%-420px)] top-4 w-px scale-x-50 origin-center bg-slate-200" />

        <div className="p-6">
          <ReportDraft embedded currentPatient={currentPatient} />
        </div>

        <div className="p-6">
          <KeyEvidence embedded currentPatient={currentPatient}/>
        </div>
      </div>
    </Card>
  );
}