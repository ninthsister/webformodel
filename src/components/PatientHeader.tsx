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
  Form,
  Input,
  InputNumber,
  Select,
  DatePicker,
  Upload,
} from "antd";
import type { UploadFile } from "antd/es/upload/interface";
import StatusDot from "@/components/StatusDot";
import type { Patient } from "@/app/main/page";
import type { Language } from "@/components/i18n";
import { buildApiUrl, getLanguageHeaders, zhEn } from "@/components/i18n";

const { Title, Text } = Typography;

type PatientHeaderProps = {
  currentPatient: Patient;
  onPatientChange: (patient: Patient) => void;
  language?: Language;
};

type AnalysisStatus = "not_started" | "analyzing" | "completed" | "failed";

type ModalityType = "MRI" | "CT" | "PET" | "PET/CT";

type UploadModalityType =
  | "MRI/T1"
  | "MRI/T1CE"
  | "MRI/T2"
  | "CT"
  | "PET"
  | "PET/CT";

const ALL_UPLOAD_MODALITIES: UploadModalityType[] = [
  "MRI/T1",
  "MRI/T1CE",
  "MRI/T2",
  "CT",
  "PET",
  "PET/CT",
];

function isMriUploadModality(value: UploadModalityType) {
  return value.startsWith("MRI/");
}

function getMriSequenceFromUploadModality(value: UploadModalityType) {
  if (value === "MRI/T1") return "T1";
  if (value === "MRI/T1CE") return "T1CE";
  if (value === "MRI/T2") return "T2";
  return "";
}

function buildEmptyUploadFileMap(): Record<UploadModalityType, UploadFile[]> {
  return {
    "MRI/T1": [],
    "MRI/T1CE": [],
    "MRI/T2": [],
    CT: [],
    PET: [],
    "PET/CT": [],
  };
}

export default function PatientHeader({
  currentPatient,
  onPatientChange,
  language = "zh",
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

  const [localUploadModalOpen, setLocalUploadModalOpen] = useState(false);

  const [localUploadLoading, setLocalUploadLoading] = useState(false);

  const [localUploadForm] = Form.useForm();

  const [selectedModalities, setSelectedModalities] = useState<
    UploadModalityType[]
  >(["MRI/T1"]);

  const [localUploadFileMap, setLocalUploadFileMap] = useState<
    Record<UploadModalityType, UploadFile[]>
  >(buildEmptyUploadFileMap());

  const [patientDataReady, setPatientDataReady] = useState(false);

  const [startAnalysisLoading, setStartAnalysisLoading] = useState(false);

  const [analysisStatus, setAnalysisStatus] =
    useState<AnalysisStatus>("not_started");

  const [analysisMessage, setAnalysisMessage] = useState<string>(
    zhEn(language, "尚未开始分析", "Analysis not started")
  );

  const hasPatientModality = (modalityName: string) => {
    return currentPatient.modalities?.includes(modalityName) ?? false;
  };

  const getClinicalHistoryStatus = () => {
    return currentPatient.clinicalHistoryStatus || "missing";
  };

  const getClinicalHistoryIcon = () => {
    const status = getClinicalHistoryStatus();

    if (status === "provided") {
      return <StatusDot />;
    }

    if (status === "partial") {
      return <ClockCircleOutlined className="text-orange-500" />;
    }

    return <ExclamationCircleFilled className="text-red-500" />;
  };

  const getClinicalHistoryText = () => {
    const status = getClinicalHistoryStatus();

    if (status === "provided") {
      return zhEn(language, "已提供", "Provided");
    }

    if (status === "partial") {
      return zhEn(language, "部分缺失", "Partly missing");
    }

    return zhEn(language, "缺失", "Missing");
  };

  const getClinicalHistoryClassName = () => {
    const status = getClinicalHistoryStatus();

    if (status === "provided") {
      return "text-slate-400";
    }

    if (status === "partial") {
      return "text-orange-400";
    }

    return "text-red-400";
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

      const res = await fetch(
        buildApiUrl("http://127.0.0.1:8000/api/patient/list", language),
        {
          method: "GET",
          headers: getLanguageHeaders(language),
        }
      );

      if (!res.ok) {
        throw new Error(
          zhEn(
            language,
            "获取服务端病人列表失败",
            "Failed to fetch server patient list"
          )
        );
      }

      const data = await res.json();

      const patients: Patient[] = Array.isArray(data)
        ? data
        : data.patients || [];

      setServerPatientList(patients);
      setSelectedServerPatientId(null);
      setServerPatientListModalOpen(true);
    } catch (error) {
      console.error(error);

      message.error(
        zhEn(
          language,
          "获取服务端病人列表失败",
          "Failed to fetch server patient list"
        )
      );
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
      message.warning(
        zhEn(language, "请先选择一个病人", "Please select a patient first")
      );
      return;
    }

    try {
      setImportSelectedPatientLoading(true);

      const res = await fetch(
        buildApiUrl(
          `http://127.0.0.1:8000/api/patient/import/${encodeURIComponent(
            selectedServerPatientId
          )}`,
          language
        ),
        {
          method: "GET",
          headers: getLanguageHeaders(language),
        }
      );

      if (!res.ok) {
        throw new Error(
          zhEn(
            language,
            "导入选中病人失败",
            "Failed to import selected patient"
          )
        );
      }

      const data = await res.json();

      const rawPatient = data.patient || data;

      const importedPatient: Patient = {
        ...rawPatient,
        id: rawPatient.id || selectedServerPatientId,
      } as Patient;

      onPatientChange(importedPatient);

      setPatientDataReady(true);

      if (importedPatient.analysis?.status) {
        setAnalysisStatus(importedPatient.analysis.status);
        setAnalysisMessage(
          importedPatient.analysis.message ||
            zhEn(language, "已读取分析状态", "Analysis status loaded")
        );
      } else {
        setAnalysisStatus("not_started");
        setAnalysisMessage(
          zhEn(language, "尚未开始分析", "Analysis not started")
        );
      }

      message.success(
        zhEn(
          language,
          "病人信息导入成功",
          "Patient information imported successfully"
        )
      );

      setServerPatientListModalOpen(false);
      setImportMethodModalOpen(false);
    } catch (error) {
      console.error(error);

      message.error(
        zhEn(
          language,
          "导入选中病人失败",
          "Failed to import selected patient"
        )
      );
    } finally {
      setImportSelectedPatientLoading(false);
    }
  };

  const openLocalUploadModal = () => {
    localUploadForm.resetFields();

    setSelectedModalities(["MRI/T1"]);
    setLocalUploadFileMap(buildEmptyUploadFileMap());

    localUploadForm.setFieldsValue({
      modalities: ["MRI/T1"],
      clinicalHistoryStatus: "missing",
      gender: "女",
    });

    setLocalUploadModalOpen(true);
  };

  const closeLocalUploadModal = () => {
    setLocalUploadModalOpen(false);
  };

  const beforeUploadNiiGz = (file: File) => {
    const isNiiGz = file.name.endsWith(".nii.gz");

    if (!isNiiGz) {
      message.error(
        zhEn(language, "只能上传 .nii.gz 文件", "Only .nii.gz files are allowed")
      );

      return Upload.LIST_IGNORE;
    }

    return false;
  };

  const updateModalityFileList = (
    modality: UploadModalityType,
    fileList: UploadFile[]
  ) => {
    setLocalUploadFileMap((prev) => ({
      ...prev,
      [modality]: fileList.slice(-1),
    }));
  };

  const removeModalityFile = (modality: UploadModalityType) => {
    setLocalUploadFileMap((prev) => ({
      ...prev,
      [modality]: [],
    }));
  };

  const submitLocalPatientUpload = async () => {
    try {
      const values = await localUploadForm.validateFields();

      const uploadModalities = (values.modalities ||
        []) as UploadModalityType[];

      if (uploadModalities.length === 0) {
        message.warning(
          zhEn(
            language,
            "请至少选择一种影像模态或 MRI 子序列",
            "Please select at least one imaging modality or MRI sequence"
          )
        );

        return;
      }

      const missingModalities = uploadModalities.filter(
        (modality) => localUploadFileMap[modality].length === 0
      );

      if (missingModalities.length > 0) {
        message.warning(
          zhEn(
            language,
            `请上传 ${missingModalities.join("、")} 对应的 .nii.gz 文件`,
            `Please upload .nii.gz files for ${missingModalities.join(", ")}`
          )
        );

        return;
      }

      setLocalUploadLoading(true);

      const formData = new FormData();

      formData.append("id", values.id);
      formData.append("name", values.name);
      formData.append("age", String(values.age));
      formData.append("gender", values.gender || "");
      formData.append("stage", values.stage || "");
      formData.append(
        "date",
        values.date ? values.date.format("YYYY-MM-DD") : ""
      );
      formData.append(
        "clinicalHistoryStatus",
        values.clinicalHistoryStatus || "missing"
      );

      const realModalities: ModalityType[] = [];
      const mriSequences: string[] = [];

      uploadModalities.forEach((item) => {
        if (isMriUploadModality(item)) {
          if (!realModalities.includes("MRI")) {
            realModalities.push("MRI");
          }

          const sequence = getMriSequenceFromUploadModality(item);

          if (sequence && !mriSequences.includes(sequence)) {
            mriSequences.push(sequence);
          }

          return;
        }

        if (!realModalities.includes(item as ModalityType)) {
          realModalities.push(item as ModalityType);
        }
      });

      formData.append("modalities", JSON.stringify(realModalities));
      formData.append("mriSequences", JSON.stringify(mriSequences));
      formData.append("uploadModalities", JSON.stringify(uploadModalities));

      uploadModalities.forEach((modality) => {
        const file = localUploadFileMap[modality][0]?.originFileObj;

        if (!file) return;

        if (modality === "MRI/T1") {
          formData.append("mri_t1_file", file);
        }

        if (modality === "MRI/T1CE") {
          formData.append("mri_t1ce_file", file);
        }

        if (modality === "MRI/T2") {
          formData.append("mri_t2_file", file);
        }

        if (modality === "CT") {
          formData.append("ct_file", file);
        }

        if (modality === "PET") {
          formData.append("pet_file", file);
        }

        if (modality === "PET/CT") {
          formData.append("petct_file", file);
        }
      });

      const res = await fetch(
        buildApiUrl(
          "http://127.0.0.1:8000/api/patient/upload-local",
          language
        ),
        {
          method: "POST",
          headers: {
            ...getLanguageHeaders(language),
          },
          body: formData,
        }
      );

      const data = await res.json();

      if (res.status === 409) {
        localUploadForm.setFields([
          {
            name: "id",
            errors: [
              data.detail ||
                zhEn(
                  language,
                  "病人 ID 已存在，请重新输入",
                  "Patient ID already exists. Please enter another one."
                ),
            ],
          },
        ]);

        message.error(
          data.detail ||
            zhEn(
              language,
              "病人 ID 已存在，请重新输入",
              "Patient ID already exists. Please enter another one."
            )
        );

        return;
      }

      if (!res.ok) {
        throw new Error(
          data.detail ||
            zhEn(
              language,
              "本地病人数据上传失败",
              "Failed to upload local patient data"
            )
        );
      }

      const uploadedPatient: Patient = data.patient || data;

      onPatientChange(uploadedPatient);

      setPatientDataReady(true);

      if (uploadedPatient.analysis?.status) {
        setAnalysisStatus(uploadedPatient.analysis.status);
        setAnalysisMessage(
          uploadedPatient.analysis.message ||
            zhEn(language, "已读取分析状态", "Analysis status loaded")
        );
      } else {
        setAnalysisStatus("not_started");
        setAnalysisMessage(
          zhEn(language, "尚未开始分析", "Analysis not started")
        );
      }

      message.success(
        zhEn(
          language,
          "本地病人数据上传成功",
          "Local patient data uploaded successfully"
        )
      );

      setLocalUploadModalOpen(false);
      setImportMethodModalOpen(false);
    } catch (error) {
      console.error(error);

      if (error instanceof Error) {
        message.error(error.message);
      } else {
        message.error(
          zhEn(
            language,
            "本地病人数据上传失败",
            "Failed to upload local patient data"
          )
        );
      }
    } finally {
      setLocalUploadLoading(false);
    }
  };

  const pollAnalysisStatus = async (patientId: string) => {
    let retryCount = 0;
    const maxRetryCount = 30;

    const timer = window.setInterval(async () => {
      try {
        retryCount += 1;

        const res = await fetch(
          buildApiUrl(
            `http://127.0.0.1:8000/api/analysis/status/${encodeURIComponent(
              patientId
            )}`,
            language
          ),
          {
            method: "GET",
            headers: getLanguageHeaders(language),
          }
        );

        if (!res.ok) {
          throw new Error(
            zhEn(
              language,
              "查询分析状态失败",
              "Failed to query analysis status"
            )
          );
        }

        const data = await res.json();

        const analysis = data.analysis;
        const status = analysis?.status as AnalysisStatus;

        setAnalysisStatus(status);
        setAnalysisMessage(
          analysis?.message || zhEn(language, "正在分析", "Analyzing")
        );

        if (status === "completed") {
          window.clearInterval(timer);
          setStartAnalysisLoading(false);

          const updatedPatient = {
            ...currentPatient,
            analysis,
          } as Patient;

          onPatientChange(updatedPatient);

          message.success(zhEn(language, "分析完成", "Analysis completed"));
        }

        if (status === "failed") {
          window.clearInterval(timer);
          setStartAnalysisLoading(false);

          onPatientChange({
            ...currentPatient,
            analysis,
          } as Patient);

          message.error(
            analysis?.message || zhEn(language, "分析失败", "Analysis failed")
          );
        }

        if (retryCount >= maxRetryCount) {
          window.clearInterval(timer);
          setStartAnalysisLoading(false);

          message.warning(
            zhEn(
              language,
              "分析时间较长，请稍后重新查看状态",
              "Analysis is taking longer than expected. Please check again later."
            )
          );
        }
      } catch (error) {
        console.error(error);

        window.clearInterval(timer);

        setStartAnalysisLoading(false);
        setAnalysisStatus("failed");
        setAnalysisMessage(
          zhEn(language, "查询分析状态失败", "Failed to query analysis status")
        );

        message.error(
          zhEn(language, "查询分析状态失败", "Failed to query analysis status")
        );
      }
    }, 1000);
  };

  const startAnalysis = async () => {
    if (!currentPatient?.id) {
      message.warning(
        zhEn(
          language,
          "当前没有可分析的病人数据",
          "No patient data is available for analysis"
        )
      );

      return;
    }

    try {
      setStartAnalysisLoading(true);
      setAnalysisStatus("analyzing");
      setAnalysisMessage(zhEn(language, "正在分析", "Analyzing"));

      const res = await fetch(
        buildApiUrl("http://127.0.0.1:8000/api/analysis/start", language),
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            ...getLanguageHeaders(language),
          },
          body: JSON.stringify({
            patientId: currentPatient.id,
            signal: "start_analysis",
            language,
          }),
        }
      );

      if (!res.ok) {
        throw new Error(
          zhEn(
            language,
            "开始分析请求失败",
            "Start analysis request failed"
          )
        );
      }

      const data = await res.json();

      if (data.analysis?.status) {
        setAnalysisStatus(data.analysis.status);
        setAnalysisMessage(
          data.analysis.message || zhEn(language, "正在分析", "Analyzing")
        );
      }

      message.success(
        zhEn(language, "已发送开始分析信号", "Start analysis signal sent")
      );

      pollAnalysisStatus(currentPatient.id);
    } catch (error) {
      console.error(error);

      setStartAnalysisLoading(false);
      setAnalysisStatus("failed");
      setAnalysisMessage(
        zhEn(language, "开始分析失败", "Failed to start analysis")
      );

      message.error(zhEn(language, "开始分析失败", "Failed to start analysis"));
    }
  };

  const exportReport = async () => {
    try {
      const res = await fetch(
        buildApiUrl("http://127.0.0.1:8000/api/report/export-demo", language),
        {
          method: "GET",
          headers: getLanguageHeaders(language),
        }
      );

      if (!res.ok) {
        throw new Error(zhEn(language, "导出失败", "Export failed"));
      }

      await res.json();

      message.success(
        zhEn(
          language,
          "成功连接后端，报告已导出",
          "Backend connected successfully. Report exported."
        )
      );
    } catch (error) {
      console.error(error);
      message.error(zhEn(language, "导出报告失败", "Failed to export report"));
    }
  };

  const getAnalysisTag = () => {
    if (analysisStatus === "analyzing") {
      return (
        <Tag color="processing">
          {zhEn(language, "正在分析", "Analyzing")}
        </Tag>
      );
    }

    if (analysisStatus === "completed") {
      return (
        <Tag color="success">
          {zhEn(language, "分析完成", "Completed")}
        </Tag>
      );
    }

    if (analysisStatus === "failed") {
      return <Tag color="error">{zhEn(language, "分析失败", "Failed")}</Tag>;
    }

    return <Tag>{zhEn(language, "未分析", "Not analyzed")}</Tag>;
  };

  return (
    <>
      <Card
        className="border-slate-200 shadow-sm"
        styles={{ body: { padding: 12 } }}
      >
        <div className="grid grid-cols-[280px_1fr_420px] gap-4">
          <div className="flex items-center gap-3">
            <div className="flex h-12 w-12 items-center justify-center rounded-full bg-blue-100 text-xl font-bold text-blue-700">
              {zhEn(language, "头像", "Avatar")}
            </div>

            <div>
              <Title level={5} className="!mb-0">
                {zhEn(language, "病人ID", "Patient ID")}:{" "}
                {currentPatient.id || "-"}
              </Title>

              <div className="grid grid-cols-2 gap-x-4 text-xs text-slate-500">
                <span>
                  {zhEn(language, "年龄", "Age")}:{" "}
                  {currentPatient.age ?? "-"}
                </span>

                <span>
                  {zhEn(language, "性别", "Sex")}:{" "}
                  {currentPatient.gender || "-"}
                </span>

                <span>
                  {zhEn(language, "阶段", "Stage")}:{" "}
                  {currentPatient.stage || "-"}
                </span>

                <span>
                  {zhEn(language, "日期", "Date")}:{" "}
                  {currentPatient.date || "-"}
                </span>
              </div>

              <div className="mt-1 flex items-center gap-2 text-xs">
                {getAnalysisTag()}
                <span className="text-slate-500">{analysisMessage}</span>
              </div>
            </div>
          </div>

          <div>
            <Text strong>
              {zhEn(language, "可用模态", "Available Modalities")}
            </Text>

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
                  {hasPatientModality("MRI")
                    ? zhEn(language, "已提供", "Provided")
                    : zhEn(language, "缺失", "Missing")}
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
                  {hasPatientModality("PET")
                    ? zhEn(language, "已提供", "Provided")
                    : zhEn(language, "缺失", "Missing")}
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
                  {hasPatientModality("PET/CT")
                    ? zhEn(language, "已提供", "Provided")
                    : zhEn(language, "缺失", "Missing")}
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
                  {hasPatientModality("CT")
                    ? zhEn(language, "已提供", "Provided")
                    : zhEn(language, "缺失", "Missing")}
                </div>
              </div>

              <div>
                {getClinicalHistoryIcon()}

                <span className="ml-1">
                  {zhEn(language, "临床病史", "Clinical History")}
                </span>

                <div className={getClinicalHistoryClassName()}>
                  {getClinicalHistoryText()}
                </div>
              </div>
            </div>
          </div>

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
                {analysisStatus === "completed"
                  ? zhEn(language, "重新分析", "Re-analyze")
                  : zhEn(language, "开始分析", "Start Analysis")}
              </Button>
            )}

            <Button
              type="primary"
              icon={<ImportOutlined />}
              className="h-12 w-36"
              onClick={openImportMethodModal}
            >
              {zhEn(language, "导入病人信息", "Import Patient Info")}
            </Button>

            <Button
              type="primary"
              icon={<DownloadOutlined />}
              className="h-12 w-32"
              onClick={exportReport}
            >
              {zhEn(language, "导出报告", "Export Report")}
            </Button>
          </div>
        </div>
      </Card>

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
              {zhEn(
                language,
                "请选择病人数据导入方式",
                "Select Patient Data Import Method"
              )}
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
                    {zhEn(language, "选择服务端数据", "Select Server Data")}
                  </div>

                  <div className="mt-1 text-xs text-slate-500">
                    {zhEn(
                      language,
                      "从后端已有病人数据中导入",
                      "Import from existing backend patient data"
                    )}
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
                  {zhEn(language, "选择 1", "Select 1")}
                </Button>
              </div>
            </Card>

            <Card
              hoverable
              className="border-slate-200 text-center transition-all hover:border-slate-400 hover:shadow-md"
              onClick={openLocalUploadModal}
            >
              <div className="flex flex-col items-center gap-3">
                <div className="flex h-14 w-14 items-center justify-center rounded-full bg-slate-100 text-2xl text-slate-600">
                  <UploadOutlined />
                </div>

                <div>
                  <div className="font-semibold text-slate-800">
                    {zhEn(language, "上传本地数据", "Upload Local Data")}
                  </div>

                  <div className="mt-1 text-xs text-slate-500">
                    {zhEn(
                      language,
                      "填写病人信息并上传多模态 .nii.gz 文件",
                      "Fill patient info and upload multi-modal .nii.gz files"
                    )}
                  </div>
                </div>

                <Button
                  onClick={(e) => {
                    e.stopPropagation();
                    openLocalUploadModal();
                  }}
                >
                  {zhEn(language, "选择 2", "Select 2")}
                </Button>
              </div>
            </Card>
          </div>
        </div>
      </Modal>

      <Modal
        title={zhEn(language, "选择服务端病人数据", "Select Server Patient Data")}
        open={serverPatientListModalOpen}
        centered
        width={680}
        okText={zhEn(language, "确认导入", "Confirm Import")}
        cancelText={zhEn(language, "返回", "Back")}
        confirmLoading={importSelectedPatientLoading}
        onOk={confirmImportSelectedServerPatient}
        onCancel={closeServerPatientListModal}
      >
        <div className="mb-3 text-sm text-slate-500">
          {zhEn(
            language,
            "请选择一个服务端已经保存的病人数据，然后点击确认导入。",
            "Select a patient saved on the server, then click Confirm Import."
          )}
        </div>

        <List
          bordered
          loading={serverPatientListLoading}
          dataSource={serverPatientList}
          locale={{
            emptyText: zhEn(language, "暂无服务端病人数据", "No server patient data"),
          }}
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
                        {patient.name ||
                          zhEn(language, "未命名病人", "Unnamed patient")}
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
                      {zhEn(language, "年龄", "Age")}：{patient.age ?? "-"}　
                      {zhEn(language, "性别", "Sex")}：
                      {patient.gender || "-"}　{zhEn(language, "日期", "Date")}：
                      {patient.date || "-"}
                    </div>

                    <div className="mt-1 text-xs text-slate-400">
                      {zhEn(language, "可用模态", "Available Modalities")}：
                      {patient.modalities && patient.modalities.length > 0
                        ? patient.modalities.join(" / ")
                        : zhEn(language, "暂无记录", "No record")}
                    </div>

                    <div className="mt-1 text-xs text-slate-400">
                      {zhEn(language, "临床病史", "Clinical History")}：
                      {patient.clinicalHistoryStatus === "provided"
                        ? zhEn(language, "已提供", "Provided")
                        : patient.clinicalHistoryStatus === "partial"
                        ? zhEn(language, "部分缺失", "Partly missing")
                        : zhEn(language, "缺失", "Missing")}
                    </div>
                  </div>
                </div>
              </List.Item>
            );
          }}
        />
      </Modal>

      <Modal
        title={zhEn(language, "上传本地病人数据", "Upload Local Patient Data")}
        open={localUploadModalOpen}
        centered
        width={820}
        okText={zhEn(language, "确认上传", "Confirm Upload")}
        cancelText={zhEn(language, "返回", "Back")}
        confirmLoading={localUploadLoading}
        onOk={submitLocalPatientUpload}
        onCancel={closeLocalUploadModal}
      >
        <div className="mb-4 text-sm text-slate-500">
          {zhEn(
            language,
            "请填写病人基本信息，并为 MRI/T1、MRI/T1CE、MRI/T2、CT、PET 或 PET/CT 分别上传对应的 .nii.gz 医学影像文件。如果病人 ID 已存在，后端会拒绝上传并要求重新输入。",
            "Please fill in patient information and upload corresponding .nii.gz files for MRI/T1, MRI/T1CE, MRI/T2, CT, PET, or PET/CT. If the patient ID already exists, the backend will reject it and ask for another ID."
          )}
        </div>

        <Form
          form={localUploadForm}
          layout="vertical"
          initialValues={{
            modalities: ["MRI/T1"],
            clinicalHistoryStatus: "missing",
            gender: "女",
          }}
        >
          <div className="grid grid-cols-2 gap-4">
            <Form.Item
              label={zhEn(language, "病人 ID", "Patient ID")}
              name="id"
              rules={[
                {
                  required: true,
                  message: zhEn(
                    language,
                    "请输入病人 ID",
                    "Please enter patient ID"
                  ),
                },
                {
                  pattern: /^[A-Za-z0-9_-]+$/,
                  message: zhEn(
                    language,
                    "病人 ID 只能包含字母、数字、下划线和短横线",
                    "Patient ID can only contain letters, numbers, underscores and hyphens"
                  ),
                },
              ]}
            >
              <Input placeholder="C-2026-0129" />
            </Form.Item>

            <Form.Item
              label={zhEn(language, "姓名", "Name")}
              name="name"
              rules={[
                {
                  required: true,
                  message: zhEn(language, "请输入姓名", "Please enter name"),
                },
              ]}
            >
              <Input
                placeholder={zhEn(
                  language,
                  "例如：测试病人2",
                  "e.g. Test Patient 2"
                )}
              />
            </Form.Item>

            <Form.Item
              label={zhEn(language, "年龄", "Age")}
              name="age"
              rules={[
                {
                  required: true,
                  message: zhEn(language, "请输入年龄", "Please enter age"),
                },
              ]}
            >
              <InputNumber min={0} max={120} className="w-full" />
            </Form.Item>

            <Form.Item label={zhEn(language, "性别", "Sex")} name="gender">
              <Select
                options={[
                  { label: zhEn(language, "女", "Female"), value: "女" },
                  { label: zhEn(language, "男", "Male"), value: "男" },
                ]}
              />
            </Form.Item>

            <Form.Item label={zhEn(language, "分期", "Stage")} name="stage">
              <Input placeholder="IB2" />
            </Form.Item>

            <Form.Item label={zhEn(language, "日期", "Date")} name="date">
              <DatePicker className="w-full" />
            </Form.Item>

            <Form.Item
              label={zhEn(
                language,
                "影像模态 / MRI 子序列",
                "Imaging Modality / MRI Sequence"
              )}
              name="modalities"
              rules={[
                {
                  required: true,
                  message: zhEn(
                    language,
                    "请至少选择一种影像模态或 MRI 子序列",
                    "Please select at least one imaging modality or MRI sequence"
                  ),
                },
              ]}
            >
              <Select
                mode="multiple"
                placeholder={zhEn(
                  language,
                  "请选择需要上传的影像模态或 MRI 子序列",
                  "Please select imaging modalities or MRI sequences"
                )}
                options={[
                  {
                    label: "MRI",
                    options: [
                      { label: "MRI / T1", value: "MRI/T1" },
                      { label: "MRI / T1CE", value: "MRI/T1CE" },
                      { label: "MRI / T2", value: "MRI/T2" },
                    ],
                  },
                  {
                    label: zhEn(language, "其他模态", "Other Modalities"),
                    options: [
                      { label: "CT", value: "CT" },
                      { label: "PET", value: "PET" },
                      { label: "PET/CT", value: "PET/CT" },
                    ],
                  },
                ]}
                onChange={(value: UploadModalityType[]) => {
                  setSelectedModalities(value);

                  setLocalUploadFileMap((prev) => {
                    const next = { ...prev };

                    ALL_UPLOAD_MODALITIES.forEach((modality) => {
                      if (!value.includes(modality)) {
                        next[modality] = [];
                      }
                    });

                    return next;
                  });
                }}
              />
            </Form.Item>

            <Form.Item
              label={zhEn(
                language,
                "临床病史状态",
                "Clinical History Status"
              )}
              name="clinicalHistoryStatus"
            >
              <Select
                options={[
                  {
                    label: zhEn(language, "缺失", "Missing"),
                    value: "missing",
                  },
                  {
                    label: zhEn(language, "部分缺失", "Partly missing"),
                    value: "partial",
                  },
                  {
                    label: zhEn(language, "已提供", "Provided"),
                    value: "provided",
                  },
                ]}
              />
            </Form.Item>
          </div>

          <div className="mt-2 rounded-lg border border-slate-200 bg-slate-50 p-4">
            <div className="mb-3 font-medium text-slate-700">
              {zhEn(
                language,
                "请为每种已选择的模态或 MRI 子序列上传对应文件",
                "Please upload the corresponding file for each selected modality or MRI sequence"
              )}
            </div>

            {selectedModalities.length === 0 ? (
              <div className="text-sm text-slate-400">
                {zhEn(
                  language,
                  "请先选择影像模态或 MRI 子序列",
                  "Please select imaging modalities or MRI sequences first"
                )}
              </div>
            ) : (
              <div className="space-y-4">
                {selectedModalities.map((modality) => (
                  <div
                    key={modality}
                    className="flex items-start justify-between gap-4 rounded-md bg-white p-3"
                  >
                    <div className="min-w-[100px] pt-1">
                      <Tag color={isMriUploadModality(modality) ? "cyan" : "blue"}>
                        {modality}
                      </Tag>
                    </div>

                    <div className="flex-1">
                      <Upload
                        beforeUpload={beforeUploadNiiGz}
                        fileList={localUploadFileMap[modality]}
                        maxCount={1}
                        accept=".nii.gz"
                        onChange={({ fileList }) => {
                          updateModalityFileList(modality, fileList);
                        }}
                        onRemove={() => {
                          removeModalityFile(modality);
                        }}
                      >
                        <Button icon={<UploadOutlined />}>
                          {zhEn(
                            language,
                            `选择 ${modality} 的 .nii.gz 文件`,
                            `Select ${modality} .nii.gz file`
                          )}
                        </Button>
                      </Upload>

                      <div className="mt-1 text-xs text-slate-400">
                        {zhEn(
                          language,
                          `请上传 ${modality} 对应的 .nii.gz 文件`,
                          `Please upload the .nii.gz file for ${modality}`
                        )}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </Form>
      </Modal>
    </>
  );
}