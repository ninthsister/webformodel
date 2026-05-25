"use client";

import { useEffect, useState } from "react";
import { message } from "antd";
import PageTopBar from "@/components/PageTopBar";
import PatientHeader from "@/components/PatientHeader";
import MRIViewer from "@/components/MRIViewer";
import AssessmentPanel from "@/components/AssessmentPanel";
import ReasoningPanel from "@/components/ReasoningPanel";
import ReportEvidencePanel from "@/components/ReportEvidencePanel";
import FeedbackActionPanel from "@/components/FeedbackActionPanel";
import { buildApiUrl, getLanguageHeaders } from "@/components/i18n";
import type { Language } from "@/components/i18n";

export type Patient = {
  id: string;
  name?: string;
  age?: number;
  gender?: string;
  stage?: string;
  date?: string;
  modalities?: string[];
  mriSequences?: string[];
  clinicalHistoryStatus?: "missing" | "partial" | "provided";
  analysis?: {
    status: "not_started" | "analyzing" | "completed" | "failed";
    message?: string;
    started_at?: string | null;
    finished_at?: string | null;
    result?: {};
  };
};

const PAGE_TEXT = {
  zh: {
    reloadFailed: "切换语言后重新读取病人信息失败",
  },
  en: {
    reloadFailed: "Failed to reload patient information after language switch",
  },
};

export default function TestPage() {
  const [language, setLanguage] = useState<Language>("zh");

  const t = PAGE_TEXT[language];

  const [currentPatient, setCurrentPatient] = useState<Patient>({
    id: "??????",
    name: "未选择病人",
    age: 0,
    gender: "未知",
    stage: "未知",
    date: "未知",
    modalities: [],
    mriSequences: [],
    clinicalHistoryStatus: "missing",
    analysis: {
      status: "not_started",
      message: "尚未开始分析",
      started_at: null,
      finished_at: null,
      result: {},
    },
  });

  useEffect(() => {
    const patientId = currentPatient.id;

    if (!patientId || patientId === "??????") {
      return;
    }

    const controller = new AbortController();

    async function reloadPatientByLanguage() {
      try {
        const res = await fetch(
          buildApiUrl(
            `http://127.0.0.1:8000/api/patient/import/${encodeURIComponent(
              patientId
            )}`,
            language
          ),
          {
            method: "GET",
            headers: getLanguageHeaders(language),
            signal: controller.signal,
          }
        );

        if (!res.ok) {
          throw new Error(`${t.reloadFailed}: ${res.status}`);
        }

        const data = await res.json();

        const rawPatient = data.patient || data;

        const nextPatient: Patient = {
          ...rawPatient,
          id: rawPatient.id || patientId,
        };

        setCurrentPatient(nextPatient);
      } catch (error) {
        if (error instanceof DOMException && error.name === "AbortError") {
          return;
        }

        console.error(error);
        message.error(t.reloadFailed);
      }
    }

    reloadPatientByLanguage();

    return () => {
      controller.abort();
    };
  }, [language, currentPatient.id, t.reloadFailed]);

  return (
    <main className="min-h-screen bg-slate-100 p-4">
      <div className="mx-auto max-w-[1600px] space-y-4">
        <PageTopBar
          language={language}
          onLanguageChange={setLanguage}
        />

        <div className="mb-6">
          <PatientHeader
            currentPatient={currentPatient}
            onPatientChange={setCurrentPatient}
            language={language}
          />
        </div>

        <div className="grid grid-cols-12 gap-4">
          <div className="col-span-5">
            <MRIViewer currentPatient={currentPatient} language={language} />
          </div>

          <div className="col-span-3">
            <AssessmentPanel
              currentPatient={currentPatient}
              language={language}
            />
          </div>

          <div className="col-span-4">
            <ReasoningPanel
              currentPatient={currentPatient}
              language={language}
            />
          </div>
        </div>

        <div className="grid grid-cols-12 gap-4">
          <div className="col-span-8">
            <ReportEvidencePanel
              currentPatient={currentPatient}
              language={language}
            />
          </div>

          <div className="col-span-4">
            <FeedbackActionPanel
              currentPatient={currentPatient}
              language={language}
            />
          </div>
        </div>
      </div>
    </main>
  );
}