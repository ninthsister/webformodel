"use client";

import { useState } from "react";
import { SaveOutlined } from "@ant-design/icons";
import { Button, Card, Typography, message } from "antd";
import type { Language } from "@/components/i18n";
import { buildApiUrl, getLanguageHeaders, zhEn } from "@/components/i18n";

const { Title } = Typography;

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

type FeedbackValue = "agree" | "partly_agree" | "disagree" | "uncertain";

const DEFAULT_FEEDBACK: FeedbackValue = "agree";

export default function DoctorFeedback({
  currentPatient,
  embedded = false,
  showTitle = true,
  language = "zh",
}: {
  currentPatient?: Patient;
  embedded?: boolean;
  showTitle?: boolean;
  language?: Language;
}) {
  const [feedback, setFeedback] = useState<FeedbackValue>(DEFAULT_FEEDBACK);
  const [comment, setComment] = useState("");
  const [saving, setSaving] = useState(false);

  const handleSave = async () => {
    const patientId = currentPatient?.id;

    if (!patientId || patientId === "??????") {
      message.warning(zhEn(language, "请先选择病人", "Please select a patient first"));
      return;
    }

    try {
      setSaving(true);

      const res = await fetch(
        buildApiUrl(
          `/api/patient/${encodeURIComponent(
            patientId
          )}/doctor-feedback`,
          language
        ),
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            ...getLanguageHeaders(language),
          },
          body: JSON.stringify({
            feedback,
            comment,
            language,
          }),
        }
      );

      if (!res.ok) {
        throw new Error(`${zhEn(language, "保存失败", "Save failed")}: ${res.status}`);
      }

      message.success(zhEn(language, "医生反馈已保存", "Doctor feedback saved"));
    } catch (error) {
      console.error("保存医生反馈失败:", error);
      message.error(zhEn(language, "保存医生反馈失败", "Failed to save doctor feedback"));
    } finally {
      setSaving(false);
    }
  };

  const handleCancel = () => {
    setFeedback(DEFAULT_FEEDBACK);
    setComment("");
  };

  const content = (
    <>
      <div className="space-y-2 text-sm">
        <label className="flex items-center gap-2">
          <input
            type="radio"
            name="feedback"
            value="agree"
            checked={feedback === "agree"}
            onChange={() => setFeedback("agree")}
          />
          {zhEn(language, "同意 AI 评估结果", "Agree with AI assessment")}
        </label>

        <label className="flex items-center gap-2">
          <input
            type="radio"
            name="feedback"
            value="partly_agree"
            checked={feedback === "partly_agree"}
            onChange={() => setFeedback("partly_agree")}
          />
          {zhEn(language, "部分同意", "Partly agree")}
        </label>

        <label className="flex items-center gap-2">
          <input
            type="radio"
            name="feedback"
            value="disagree"
            checked={feedback === "disagree"}
            onChange={() => setFeedback("disagree")}
          />
          {zhEn(language, "不同意", "Disagree")}
        </label>

        <label className="flex items-center gap-2">
          <input
            type="radio"
            name="feedback"
            value="uncertain"
            checked={feedback === "uncertain"}
            onChange={() => setFeedback("uncertain")}
          />
          {zhEn(language, "不确定", "Uncertain")}
        </label>
      </div>

      <textarea
        className="mt-4 h-20 w-full rounded border border-slate-300 p-2 text-sm outline-none focus:border-blue-500"
        placeholder={zhEn(language, "请输入医生意见或补充说明...", "Enter doctor comments or additional notes...")}
        value={comment}
        onChange={(event) => setComment(event.target.value)}
      />

      <div className="mt-3 flex gap-2">
        <Button
          type="primary"
          icon={<SaveOutlined />}
          loading={saving}
          onClick={handleSave}
        >
          {zhEn(language, "保存", "Save")}
        </Button>

        <Button onClick={handleCancel}>{zhEn(language, "取消", "Cancel")}</Button>
      </div>
    </>
  );

  if (embedded) {
    return (
      <div>
        {showTitle && (
          <Title level={4} className="!mb-5">
            {zhEn(language, "医生反馈", "Doctor Feedback")}
          </Title>
        )}
        {content}
      </div>
    );
  }

  return (
    <Card title={zhEn(language, "医生反馈", "Doctor Feedback")} className="h-full shadow-sm">
      {content}
    </Card>
  );
}