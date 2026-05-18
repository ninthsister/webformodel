import { CheckCircleFilled } from "@ant-design/icons";

type StatusDotProps = {
  type?: "success" | "warning" | "error" | "info";
};

export default function StatusDot({ type = "success" }: StatusDotProps) {
  const colorMap = {
    success: "text-green-500",
    warning: "text-orange-500",
    error: "text-red-500",
    info: "text-blue-500",
  };

  return <CheckCircleFilled className={colorMap[type]} />;
}