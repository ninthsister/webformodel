"use client";

import { AlertOutlined, FileTextOutlined } from "@ant-design/icons";
import { Button, Card, Space, Typography } from "antd";

const { Title } = Typography;

export default function ActionPanel({
  embedded = false,
  showTitle = true,
}: {
  embedded?: boolean;
  showTitle?: boolean;
}) {
  const content = (
    <Space orientation="vertical" className="w-full">
      <Button block type="primary" icon={<FileTextOutlined />}>
        插入报告
      </Button>

      <Button block>编辑报告</Button>

      <Button
        block
        danger
        icon={<AlertOutlined />}
        className="h-auto min-h-12 whitespace-normal"
      >
        <span className="flex flex-col items-center leading-5">
          <span>请求补充</span>
          <span>检查</span>
        </span>
      </Button>
    </Space>
  );

  if (embedded) {
    return (
      <div>
        {showTitle && (
          <Title level={4} className="!mb-5">
            操作
          </Title>
        )}

        {content}
      </div>
    );
  }

  return (
    <Card title="操作" className="h-full shadow-sm">
      {content}
    </Card>
  );
}