"use client";

import { useState } from "react";
import { Tag, Typography } from "antd";
import PatientHeader from "@/components/PatientHeader";
import MRIViewer from "@/components/MRIViewer";
import AssessmentPanel from "@/components/AssessmentPanel";
import ReasoningPanel from "@/components/ReasoningPanel";
import ReportEvidencePanel from "@/components/ReportEvidencePanel";
import FeedbackActionPanel from "@/components/FeedbackActionPanel";

const { Title, Text } = Typography;

/**
 * 当前病人类型
 *
 * 这个类型需要和后端返回的 patient 字段尽量保持一致。
 * gender 和 sex 都保留，是为了兼容后端有时返回 gender，有时前端使用 sex。
 */
export type Patient = {
  id: string;
  name?: string;
  age?: number;
  sex?: string;
  gender?: string;
  stage?: string;
  date?: string;
  modalities?: string[];
  analysis?: {
    status: "not_started" | "analyzing" | "completed" | "failed";
    message?: string;
    started_at?: string | null;
    finished_at?: string | null;
    result?: {
    };
  };
};

export default function TestPage() {
  /**
   * 当前页面正在展示的病人
   *
   * 这里是整个页面的“唯一病人状态”。
   * 之后 PatientHeader、MRIViewer、AssessmentPanel 等组件都从这里拿当前病人。
   */
  const [currentPatient, setCurrentPatient] = useState<Patient>({
    id: "??????",
    name: "未选择病人",
    age: 0,
    sex: "未知",
    stage: "未知",
    date: "未知",
    modalities: [],
    analysis: {
      status: "not_started",
      message: "尚未开始分析",
      started_at:  null,
      finished_at:  null,
      result: {},
    },
  });

  return (
    <main className="min-h-screen bg-slate-100 p-4">
      <div className="mx-auto max-w-[1600px] space-y-4">
        {/* 页面顶部标题栏 */}
        <div className="flex items-center justify-between">
          <div>
            <Title level={3} className="!mb-0">
              医学诊疗系统
            </Title>

            <Text type="secondary">
              PLNM & PMI Risk Assessment with Evidence Check
            </Text>
          </div>

          <Tag color="blue" className="px-3 py-1">
            AI for Clinical Use Only
          </Tag>
        </div>

        {/* 顶部病人信息栏 */}
        <div className="mb-6">
          <PatientHeader
            currentPatient={currentPatient}
            onPatientChange={setCurrentPatient}
          />
        </div>

        {/* 第一行主体区域 */}
        <div className="grid grid-cols-12 gap-4">
          <div className="col-span-5">
            <MRIViewer currentPatient={currentPatient} />
          </div>

          <div className="col-span-3">
            <AssessmentPanel currentPatient={currentPatient} />
          </div>

          <div className="col-span-4">
            <ReasoningPanel currentPatient={currentPatient} />
          </div>
        </div>

        {/* 第二行结果与操作区域 */}
        <div className="grid grid-cols-12 gap-4">
          <div className="col-span-8">
            <ReportEvidencePanel currentPatient={currentPatient}/>
          </div>

          <div className="col-span-4">
            <FeedbackActionPanel currentPatient={currentPatient} />
          </div>
        </div>
      </div>
    </main>
  );
}