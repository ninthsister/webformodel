"use client";

import { Card } from "antd";
import DoctorFeedback from "@/components/DoctorFeedback";
import ActionPanel from "@/components/ActionPanel";
import type { Language } from "@/components/i18n";
import { zhEn } from "@/components/i18n";

type Patient = {
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
    result?: {};
  };
};

export default function FeedbackActionPanel({
  currentPatient,
  language = "zh",
}: {
  currentPatient: Patient;
  language?: Language;
}) {
  return (
    <Card
      className="h-full shadow-sm"
      title={
        <div className="grid grid-cols-[1fr_200px]">
          <div className="px-6">{zhEn(language, "医生反馈", "Doctor Feedback")}</div>
          <div className="border-l border-slate-200 px-6">{zhEn(language, "操作", "Actions")}</div>
        </div>
      }
    >
      <div className="relative grid h-full grid-cols-[1fr_200px]">
        <div className="p-6">
          <DoctorFeedback
            currentPatient={currentPatient}
            embedded
            showTitle={false}
            language={language}
          />
        </div>

        <div className="border-l border-slate-200 px-6">
          <ActionPanel embedded showTitle={false} language={language} />
        </div>
      </div>
    </Card>
  );
}