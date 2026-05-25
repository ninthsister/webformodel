"use client";

import { Select, Tag, Typography } from "antd";
import type { Language } from "@/components/i18n";

const { Title, Text } = Typography;

type PageTopBarProps = {
  language: Language;
  onLanguageChange: (language: Language) => void;
};

const PAGE_TEXT = {
  zh: {
    title: "医学诊疗系统",
    subtitle: "PLNM 与 PMI 风险评估及证据核查",
    tag: "仅供临床辅助使用",
    language: "语言",
    chinese: "中文",
    english: "English",
  },
  en: {
    title: "Medical Diagnosis System",
    subtitle: "PLNM & PMI Risk Assessment with Evidence Check",
    tag: "AI for Clinical Use Only",
    language: "Language",
    chinese: "中文",
    english: "English",
  },
};

export default function PageTopBar({
  language,
  onLanguageChange,
}: PageTopBarProps) {
  const t = PAGE_TEXT[language];

  return (
    <div className="flex items-center justify-between">
      <div>
        <Title level={3} className="!mb-0">
          {t.title}
        </Title>

        <Text type="secondary">{t.subtitle}</Text>
      </div>

      <div className="flex items-center gap-3">
        <div className="flex items-center gap-2">
          <Text type="secondary">{t.language}</Text>

          <Select
            value={language}
            onChange={(value) => onLanguageChange(value)}
            style={{ width: 120 }}
            options={[
              {
                value: "zh",
                label: t.chinese,
              },
              {
                value: "en",
                label: t.english,
              },
            ]}
          />
        </div>

        <Tag color="blue" className="px-3 py-1">
          {t.tag}
        </Tag>
      </div>
    </div>
  );
}