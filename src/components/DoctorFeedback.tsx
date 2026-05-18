"use client";

import { useState } from "react";
import { SaveOutlined } from "@ant-design/icons";
import { Button, Card, Typography, message } from "antd";

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
}: {
  currentPatient?: Patient;
  embedded?: boolean;
  showTitle?: boolean;
}) {
  const [feedback, setFeedback] = useState<FeedbackValue>(DEFAULT_FEEDBACK);
  const [comment, setComment] = useState("");
  const [saving, setSaving] = useState(false);

  const handleSave = async () => {
    const patientId = currentPatient?.id;

    if (!patientId || patientId === "??????") {
      message.warning("请先选择病人");
      return;
    }

    try {
      setSaving(true);

      const res = await fetch(
        `http://127.0.0.1:8000/api/patient/${encodeURIComponent(
          patientId
        )}/doctor-feedback`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            feedback,
            comment,
          }),
        }
      );

      if (!res.ok) {
        throw new Error(`保存失败：${res.status}`);
      }

      message.success("医生反馈已保存");
    } catch (error) {
      console.error("保存医生反馈失败:", error);
      message.error("保存医生反馈失败");
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
          同意 AI 评估结果
        </label>

        <label className="flex items-center gap-2">
          <input
            type="radio"
            name="feedback"
            value="partly_agree"
            checked={feedback === "partly_agree"}
            onChange={() => setFeedback("partly_agree")}
          />
          部分同意
        </label>

        <label className="flex items-center gap-2">
          <input
            type="radio"
            name="feedback"
            value="disagree"
            checked={feedback === "disagree"}
            onChange={() => setFeedback("disagree")}
          />
          不同意
        </label>

        <label className="flex items-center gap-2">
          <input
            type="radio"
            name="feedback"
            value="uncertain"
            checked={feedback === "uncertain"}
            onChange={() => setFeedback("uncertain")}
          />
          不确定
        </label>
      </div>

      <textarea
        className="mt-4 h-20 w-full rounded border border-slate-300 p-2 text-sm outline-none focus:border-blue-500"
        placeholder="请输入医生意见或补充说明..."
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
          保存
        </Button>

        <Button onClick={handleCancel}>取消</Button>
      </div>
    </>
  );

  if (embedded) {
    return (
      <div>
        {showTitle && (
          <Title level={4} className="!mb-5">
            医生反馈
          </Title>
        )}
        {content}
      </div>
    );
  }

  return (
    <Card title="医生反馈" className="h-full shadow-sm">
      {content}
    </Card>
  );
}