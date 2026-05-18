"use client";

import { useEffect, useState } from "react";
import {
  ClockCircleOutlined,
  DownloadOutlined,
  ExclamationCircleFilled,
  ImportOutlined,
  DatabaseOutlined,
  UploadOutlined,
  PlayCircleOutlined,
} from "@ant-design/icons";
import {
  Button,
  Card,
  Typography,
  message,
  Modal,
  List,
  Radio,
  Tag,
} from "antd";
import StatusDot from "@/components/StatusDot";
import type { Patient } from "@/app/main/page";

const { Title, Text } = Typography;

type PatientHeaderProps = {
  currentPatient: Patient;
  onPatientChange: (patient: Patient) => void;
};

type AnalysisStatus = "not_started" | "analyzing" | "completed" | "failed";

export default function PatientHeader({
  currentPatient,
  onPatientChange,
}: PatientHeaderProps) {
  useEffect(() => {
    console.log("当前 currentPatient 数据：", currentPatient);
  }, [currentPatient]);
  const [importMethodModalOpen, setImportMethodModalOpen] = useState(false);

  const [serverPatientListModalOpen, setServerPatientListModalOpen] =
    useState(false);

  const [serverPatientList, setServerPatientList] = useState<Patient[]>([]);

  const [selectedServerPatientId, setSelectedServerPatientId] = useState<
    string | null
  >(null);

  const [serverPatientListLoading, setServerPatientListLoading] =
    useState(false);

  const [importSelectedPatientLoading, setImportSelectedPatientLoading] =
    useState(false);

  /**
   * 是否已经导入/上传了病人数据
   */
  const [patientDataReady, setPatientDataReady] = useState(false);

  /**
   * 点击“开始分析”按钮时的 loading
   */
  const [startAnalysisLoading, setStartAnalysisLoading] = useState(false);

  /**
   * 当前分析状态
   */
  const [analysisStatus, setAnalysisStatus] =
    useState<AnalysisStatus>("not_started");

  /**
   * 当前分析提示信息
   */
  const [analysisMessage, setAnalysisMessage] = useState<string>("尚未开始分析");

  const hasPatientModality = (modalityName: string) => {
    return currentPatient.modalities?.includes(modalityName) ?? false;
  };

  const openImportMethodModal = () => {
    setImportMethodModalOpen(true);
  };

  const closeImportMethodModal = () => {
    setImportMethodModalOpen(false);
  };

  const openServerPatientListModal = async () => {
    try {
      setServerPatientListLoading(true);

      const res = await fetch("http://127.0.0.1:8000/api/patient/list", {
        method: "GET",
      });

      if (!res.ok) {
        throw new Error("获取服务端病人列表失败");
      }

      const data = await res.json();

      console.log("后端原始返回 data：", data);

      const patients: Patient[] = Array.isArray(data)
        ? data
        : data.patients || [];

      /**
       * 这里不再做任何标准化
       * 后端 info.json 里有什么字段，前端就直接接收什么字段
       */
      console.log("直接使用的 patients：", patients);

      /**
       * 单独打印每个病人的完整信息，方便观察 analysis 字段
       */

      setServerPatientList(patients);

      setSelectedServerPatientId(null);
      setServerPatientListModalOpen(true);
    } catch (error) {
      console.error(error);
      message.error("获取服务端病人列表失败");
    } finally {
      setServerPatientListLoading(false);
    }
  };

  const closeServerPatientListModal = () => {
    setServerPatientListModalOpen(false);
  };

  const selectServerPatient = (patientId: string) => {
    setSelectedServerPatientId(patientId);
  };

  const confirmImportSelectedServerPatient = async () => {
    if (!selectedServerPatientId) {
      message.warning("请先选择一个病人");
      return;
    }

    try {
      setImportSelectedPatientLoading(true);

      const res = await fetch(
        `http://127.0.0.1:8000/api/patient/import/${selectedServerPatientId}`,
        {
          method: "GET",
        }
      );

      if (!res.ok) {
        throw new Error("导入选中病人失败");
      }

      const data = await res.json();

      console.log("导入选中病人接口原始返回:", data);

      /**
       * 后端如果返回：
       * {
       *   message: "...",
       *   patient: {...},
       *   paths: {...}
       * }
       *
       * 那么这里直接使用 data.patient。
       *
       * 如果后端直接返回病人 JSON，
       * 那么这里直接使用 data。
       */
      const rawPatient = data.patient || data;

      /**
       * 直接使用后端返回的病人 JSON 数据
       * 不再重新组装字段，避免 analysis 等字段丢失
       */
      const importedPatient: Patient = {
        ...rawPatient,

        /**
         * 最小兜底：
         * 如果 info.json 里面没有 id，就用当前选择的文件夹 ID
         */
        id: rawPatient.id || selectedServerPatientId,
      } as Patient;

      console.log("最终写入 currentPatient 的 importedPatient:", importedPatient);
      console.log("导入后的 analysis:", importedPatient.analysis);

      /**
       * 直接覆盖父组件 currentPatient
       */
      onPatientChange(importedPatient);

      setPatientDataReady(true);

      /**
       * 根据 importedPatient.analysis 更新前端分析状态
       */
      if (importedPatient.analysis?.status) {
        setAnalysisStatus(importedPatient.analysis.status);
        setAnalysisMessage(
          importedPatient.analysis.message || "已读取分析状态"
        );
      } else {
        setAnalysisStatus("not_started");
        setAnalysisMessage("尚未开始分析");
      }

      message.success("病人信息导入成功");

      setServerPatientListModalOpen(false);
      setImportMethodModalOpen(false);
    } catch (error) {
      console.error(error);
      message.error("导入选中病人失败");
    } finally {
      setImportSelectedPatientLoading(false);
    }
  };

  const openUploadPatientDataPlaceholder = () => {
    message.info("上传数据功能后续实现");
  };

  /**
   * 轮询后端分析状态
   *
   * 后端接口：
   * GET /api/analysis/status/{patient_id}
   */
  const pollAnalysisStatus = async (patientId: string) => {
    let retryCount = 0;
    const maxRetryCount = 30;

    const timer = window.setInterval(async () => {
      try {
        retryCount += 1;

        const res = await fetch(
          `http://127.0.0.1:8000/api/analysis/status/${patientId}`,
          {
            method: "GET",
          }
        );

        if (!res.ok) {
          throw new Error("查询分析状态失败");
        }

        const data = await res.json();

        console.log("分析状态返回:", data);

        const analysis = data.analysis;
        const status = analysis?.status as AnalysisStatus;

        setAnalysisStatus(status);
        setAnalysisMessage(analysis?.message || "正在分析");

        /**
         * 分析完成
         */
        if (status === "completed") {
          window.clearInterval(timer);

          setStartAnalysisLoading(false);

          onPatientChange({
            ...currentPatient,
            analysis,
          } as Patient);
          const updatedPatient = {
            ...currentPatient,
            analysis,
          } as Patient;
          console.log("分析完成后的 currentPatient：", updatedPatient);
          message.success("分析完成");
        }

        /**
         * 分析失败
         */
        if (status === "failed") {
          window.clearInterval(timer);

          setStartAnalysisLoading(false);

          onPatientChange({
            ...currentPatient,
            analysis,
          } as Patient);

          message.error(analysis?.message || "分析失败");
        }

        /**
         * 超时保护
         */
        if (retryCount >= maxRetryCount) {
          window.clearInterval(timer);

          setStartAnalysisLoading(false);

          message.warning("分析时间较长，请稍后重新查看状态");
        }
      } catch (error) {
        console.error(error);

        window.clearInterval(timer);

        setStartAnalysisLoading(false);
        setAnalysisStatus("failed");
        setAnalysisMessage("查询分析状态失败");

        message.error("查询分析状态失败");
      }
    }, 1000);
  };

  /**
   * 开始分析
   */
  const startAnalysis = async () => {
    if (!currentPatient?.id) {
      message.warning("当前没有可分析的病人数据");
      return;
    }

    try {
      setStartAnalysisLoading(true);
      setAnalysisStatus("analyzing");
      setAnalysisMessage("正在分析");

      const res = await fetch("http://127.0.0.1:8000/api/analysis/start", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          patientId: currentPatient.id,
          signal: "start_analysis",
        }),
      });

      if (!res.ok) {
        throw new Error("开始分析请求失败");
      }

      const data = await res.json();

      console.log("开始分析返回:", data);

      if (data.analysis?.status) {
        setAnalysisStatus(data.analysis.status);
        setAnalysisMessage(data.analysis.message || "正在分析");
      }

      message.success("已发送开始分析信号");

      /**
       * 开始轮询分析状态
       */
      pollAnalysisStatus(currentPatient.id);
    } catch (error) {
      console.error(error);

      setStartAnalysisLoading(false);
      setAnalysisStatus("failed");
      setAnalysisMessage("开始分析失败");

      message.error("开始分析失败");
    }
  };

  const exportReport = async () => {
    try {
      const res = await fetch("http://127.0.0.1:8000/api/report/export-demo", {
        method: "GET",
      });

      if (!res.ok) {
        throw new Error("导出失败");
      }

      const data = await res.json();

      console.log("导出报告返回:", data);
      message.success("成功连接后端，报告已导出");
    } catch (error) {
      console.error(error);
      message.error("导出报告失败");
    }
  };

  const getAnalysisTag = () => {
    if (analysisStatus === "analyzing") {
      return <Tag color="processing">正在分析</Tag>;
    }

    if (analysisStatus === "completed") {
      return <Tag color="success">分析完成</Tag>;
    }

    if (analysisStatus === "failed") {
      return <Tag color="error">分析失败</Tag>;
    }

    return <Tag>未分析</Tag>;
  };

  return (
    <>
      <Card
        className="border-slate-200 shadow-sm"
        styles={{ body: { padding: 12 } }}
      >
        <div className="grid grid-cols-[280px_1fr_420px] gap-4">
          {/* 左侧：病人基本信息 */}
          <div className="flex items-center gap-3">
            <div className="flex h-12 w-12 items-center justify-center rounded-full bg-blue-100 text-xl font-bold text-blue-700">
              头像
            </div>

            <div>
              <Title level={5} className="!mb-0">
                病人ID:{currentPatient.id}
              </Title>

              <div className="grid grid-cols-2 gap-x-4 text-xs text-slate-500">
                <span>年龄: {currentPatient.age ?? "-"}</span>

                <span>
                  性别: {currentPatient.sex || currentPatient.gender || "-"}
                </span>

                <span>阶段: {currentPatient.stage || "-"}</span>

                <span>日期: {currentPatient.date || "-"}</span>
              </div>

              <div className="mt-1 flex items-center gap-2 text-xs">
                {getAnalysisTag()}
                <span className="text-slate-500">{analysisMessage}</span>
              </div>
            </div>
          </div>

          {/* 中间：可用模态 */}
          <div>
            <Text strong>可用模态</Text>

            <div className="mt-2 grid grid-cols-5 gap-3 text-xs">
              <div>
                {hasPatientModality("MRI") ? (
                  <StatusDot />
                ) : (
                  <ExclamationCircleFilled className="text-red-500" />
                )}
                <span className="ml-1">MRI</span>
                <div
                  className={
                    hasPatientModality("MRI")
                      ? "text-slate-400"
                      : "text-red-400"
                  }
                >
                  {hasPatientModality("MRI") ? "已提供" : "缺失"}
                </div>
              </div>

              <div>
                {hasPatientModality("PET") ? (
                  <StatusDot type="success" />
                ) : (
                  <ExclamationCircleFilled className="text-red-500" />
                )}
                <span className="ml-1">PET</span>
                <div
                  className={
                    hasPatientModality("PET")
                      ? "text-slate-400"
                      : "text-red-400"
                  }
                >
                  {hasPatientModality("PET") ? "已提供" : "缺失"}
                </div>
              </div>

              <div>
                {hasPatientModality("PET/CT") ? (
                  <StatusDot />
                ) : (
                  <ExclamationCircleFilled className="text-red-500" />
                )}
                <span className="ml-1">PET/CT</span>
                <div
                  className={
                    hasPatientModality("PET/CT")
                      ? "text-slate-400"
                      : "text-red-400"
                  }
                >
                  {hasPatientModality("PET/CT") ? "已提供" : "缺失"}
                </div>
              </div>

              <div>
                {hasPatientModality("CT") ? (
                  <StatusDot />
                ) : (
                  <ExclamationCircleFilled className="text-red-500" />
                )}
                <span className="ml-1">CT</span>
                <div
                  className={
                    hasPatientModality("CT")
                      ? "text-slate-400"
                      : "text-red-400"
                  }
                >
                  {hasPatientModality("CT") ? "已提供" : "缺失"}
                </div>
              </div>

              <div>
                {hasPatientModality("Clinical History") ||
                hasPatientModality("临床病史") ? (
                  <StatusDot />
                ) : (
                  <ClockCircleOutlined className="text-orange-500" />
                )}
                <span className="ml-1">临床病史</span>
                <div
                  className={
                    hasPatientModality("Clinical History") ||
                    hasPatientModality("临床病史")
                      ? "text-slate-400"
                      : "text-orange-400"
                  }
                >
                  {hasPatientModality("Clinical History") ||
                  hasPatientModality("临床病史")
                    ? "已提供"
                    : "部分缺失"}
                </div>
              </div>
            </div>
          </div>

          {/* 右侧：操作按钮 */}
          <div className="flex items-center justify-end gap-2">
            {patientDataReady && (
              <Button
                type="primary"
                icon={<PlayCircleOutlined />}
                className="h-12 w-32"
                loading={startAnalysisLoading}
                disabled={analysisStatus === "analyzing"}
                onClick={startAnalysis}
              >
                {analysisStatus === "completed" ? "重新分析" : "开始分析"}
              </Button>
            )}

            <Button
              type="primary"
              icon={<ImportOutlined />}
              className="h-12 w-36"
              onClick={openImportMethodModal}
            >
              导入病人信息
            </Button>

            <Button
              type="primary"
              icon={<DownloadOutlined />}
              className="h-12 w-32"
              onClick={exportReport}
            >
              导出报告
            </Button>
          </div>
        </div>
      </Card>

      {/* 第一层弹窗：选择导入方式 */}
      <Modal
        title={null}
        open={importMethodModalOpen}
        footer={null}
        centered
        width={520}
        onCancel={closeImportMethodModal}
      >
        <div className="py-2">
          <div className="mb-6 text-center">
            <Title level={4} className="!mb-1">
              请选择病人数据导入方式
            </Title>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <Card
              hoverable
              className="border-blue-200 text-center transition-all hover:border-blue-500 hover:shadow-md"
              onClick={openServerPatientListModal}
            >
              <div className="flex flex-col items-center gap-3">
                <div className="flex h-14 w-14 items-center justify-center rounded-full bg-blue-100 text-2xl text-blue-600">
                  <DatabaseOutlined />
                </div>

                <div>
                  <div className="font-semibold text-slate-800">
                    选择服务端数据
                  </div>

                  <div className="mt-1 text-xs text-slate-500">
                    从后端已有病人数据中导入
                  </div>
                </div>

                <Button
                  type="primary"
                  loading={serverPatientListLoading}
                  onClick={(e) => {
                    e.stopPropagation();
                    openServerPatientListModal();
                  }}
                >
                  选择 1
                </Button>
              </div>
            </Card>

            <Card
              hoverable
              className="border-slate-200 text-center transition-all hover:border-slate-400 hover:shadow-md"
              onClick={openUploadPatientDataPlaceholder}
            >
              <div className="flex flex-col items-center gap-3">
                <div className="flex h-14 w-14 items-center justify-center rounded-full bg-slate-100 text-2xl text-slate-600">
                  <UploadOutlined />
                </div>

                <div>
                  <div className="font-semibold text-slate-800">
                    上传本地数据
                  </div>

                  <div className="mt-1 text-xs text-slate-500">
                    上传 MRI、CT 或临床文件
                  </div>
                </div>

                <Button
                  onClick={(e) => {
                    e.stopPropagation();
                    openUploadPatientDataPlaceholder();
                  }}
                >
                  选择 2
                </Button>
              </div>
            </Card>
          </div>
        </div>
      </Modal>

      {/* 第二层弹窗：服务端病人列表 */}
      <Modal
        title="选择服务端病人数据"
        open={serverPatientListModalOpen}
        centered
        width={680}
        okText="确认导入"
        cancelText="返回"
        confirmLoading={importSelectedPatientLoading}
        onOk={confirmImportSelectedServerPatient}
        onCancel={closeServerPatientListModal}
      >
        <div className="mb-3 text-sm text-slate-500">
          请选择一个服务端已经保存的病人数据，然后点击“确认导入”。
        </div>

        <List
          bordered
          loading={serverPatientListLoading}
          dataSource={serverPatientList}
          locale={{ emptyText: "暂无服务端病人数据" }}
          renderItem={(patient) => {
            const isSelected = selectedServerPatientId === patient.id;

            return (
              <List.Item
                className={`cursor-pointer transition-all ${
                  isSelected ? "bg-blue-50" : "hover:bg-slate-50"
                }`}
                onClick={() => selectServerPatient(patient.id)}
              >
                <div className="flex w-full items-center gap-3">
                  <Radio checked={isSelected} />

                  <div className="flex-1">
                    <div className="flex items-center gap-2">
                      <span className="font-semibold text-slate-800">
                        {patient.name || "未命名病人"}
                      </span>

                      <span className="text-sm text-slate-500">
                        {patient.id}
                      </span>

                      {patient.stage && (
                        <Tag color="blue" className="ml-1">
                          {patient.stage}
                        </Tag>
                      )}
                    </div>

                    <div className="mt-1 text-xs text-slate-500">
                      年龄：{patient.age ?? "-"}　 性别：
                      {patient.sex || patient.gender || "-"}　 日期：
                      {patient.date || "-"}
                    </div>

                    <div className="mt-1 text-xs text-slate-400">
                      可用模态：
                      {patient.modalities && patient.modalities.length > 0
                        ? patient.modalities.join(" / ")
                        : "暂无记录"}
                    </div>
                  </div>
                </div>
              </List.Item>
            );
          }}
        />
      </Modal>
    </>
  );
}