"use client";

import { AlertOutlined, FileTextOutlined } from "@ant-design/icons";
import { Button, Card, Space, Typography } from "antd";
import type { Language } from "@/components/i18n";
import { zhEn } from "@/components/i18n";

const { Title } = Typography;

export default function ActionPanel({
  embedded = false,
  showTitle = true,
  language = "zh",
}: {
  embedded?: boolean;
  showTitle?: boolean;
  language?: Language;
}) {
  const content = (
    <Space orientation="vertical" className="w-full">
      <Button block type="primary" icon={<FileTextOutlined />}>
        {zhEn(language, "插入报告", "Insert Report")}
      </Button>

      <Button block>{zhEn(language, "编辑报告", "Edit Report")}</Button>

      <Button
        block
        danger
        icon={<AlertOutlined />}
        className="h-auto min-h-12 whitespace-normal"
      >
        <span className="flex flex-col items-center leading-5">
          <span>{zhEn(language, "请求补充", "Request Additional")}</span>
          <span>{zhEn(language, "检查", "Check")}</span>
        </span>
      </Button>
    </Space>
  );

  if (embedded) {
    return (
      <div>
        {showTitle && (
          <Title level={4} className="!mb-5">
            {zhEn(language, "操作", "Actions")}
          </Title>
        )}

        {content}
      </div>
    );
  }

  return (
    <Card title={zhEn(language, "操作", "Actions")} className="h-full shadow-sm">
      {content}
    </Card>
  );
}