"use client";

import { Card } from "antd";
import DoctorFeedback from "@/components/DoctorFeedback";
import ActionPanel from "@/components/ActionPanel";

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
}: {
  currentPatient: Patient;
}) {
  return (
    <Card
      className="h-full shadow-sm"
      title={
        <div className="grid grid-cols-[1fr_200px]">
          <div className="px-6">医生反馈</div>
          <div className="border-l border-slate-200 px-6">操作</div>
        </div>
      }
    >
      <div className="relative grid h-full grid-cols-[1fr_200px]">
        <div className="p-6">
          <DoctorFeedback
            currentPatient={currentPatient}
            embedded
            showTitle={false}
          />
        </div>

        <div className="border-l border-slate-200 px-6">
          <ActionPanel embedded showTitle={false} />
        </div>
      </div>
    </Card>
  );
}