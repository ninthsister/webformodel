"use client";

import { useEffect, useMemo, useState } from "react";
import {
  InfoCircleOutlined,
  MedicineBoxOutlined,
  PlusCircleOutlined,
  ReloadOutlined,
  ScanOutlined,
} from "@ant-design/icons";
import { Button, Card, Space, Spin, Tag } from "antd";
import type { Patient } from "@/app/main/page";

type MRIViewerProps = {
  currentPatient?: Patient;
};

type PatientImage = {
  id?: string;
  url: string;
  modality?: string;
  sequence?: string;
  sliceIndex?: number;
  totalSlices?: number;
};

type PatientImageResponse = {
  patientId: string;
  images: PatientImage[];
};

const defaultPatient: Patient = {
  id: "??????",
  name: "未选择病人",
  age: 0,
  sex: "未知",
  stage: "未知",
  date: "未知",
  modalities: [],
};

const DEFAULT_MODALITIES = ["MRI", "PET", "CT", "PET/CT"];

export default function MRIViewer({
  currentPatient = defaultPatient,
}: MRIViewerProps) {
  const [images, setImages] = useState<PatientImage[]>([]);
  const [currentImageIndex, setCurrentImageIndex] = useState(0);
  const [activeModality, setActiveModality] = useState("MRI");
  const [loading, setLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState("");

  const patientId = currentPatient?.id || "??????";

  const hasValidPatient = patientId !== "??????" && patientId.trim() !== "";

  const modalities = useMemo(() => {
    if (currentPatient?.modalities && currentPatient.modalities.length > 0) {
      return currentPatient.modalities;
    }

    return DEFAULT_MODALITIES;
  }, [currentPatient]);

  const filteredImages = useMemo(() => {
    const result = images.filter((item) => {
      if (!item.modality) return true;
      return item.modality === activeModality;
    });

    return result.length > 0 ? result : images;
  }, [images, activeModality]);

  const currentImage = filteredImages[currentImageIndex];

  useEffect(() => {
    if (!hasValidPatient) {
      setImages([]);
      setCurrentImageIndex(0);
      setErrorMsg("");
      return;
    }

    const controller = new AbortController();

    const fetchPatientImages = async () => {
      try {
        setLoading(true);
        setErrorMsg("");
        setCurrentImageIndex(0);

        const res = await fetch(
          `http://127.0.0.1:8000/api/patient/${patientId}/images`,
          {
            method: "GET",
            signal: controller.signal,
          }
        );

        if (!res.ok) {
          throw new Error(`请求失败：${res.status}`);
        }

        const data: PatientImageResponse = await res.json();

        setImages(data.images || []);
      } catch (error) {
        if (error instanceof DOMException && error.name === "AbortError") {
          return;
        }

        console.error(error);
        setImages([]);
        setErrorMsg("影像数据加载失败，请检查后台接口或病人 ID。");
      } finally {
        setLoading(false);
      }
    };

    fetchPatientImages();

    return () => {
      controller.abort();
    };
  }, [patientId, hasValidPatient]);

  useEffect(() => {
    setCurrentImageIndex(0);
  }, [activeModality]);

  return (
    <Card
      className="h-full overflow-hidden border-slate-700 bg-slate-950 shadow-xl"
      styles={{
        body: {
          padding: 0,
          height: "100%",
          display: "flex",
          flexDirection: "column",
          background: "#020617",
        },
      }}
    >
      {/* 顶部影像类型切换栏 */}
      <div className="flex items-center justify-between border-b border-slate-700 bg-slate-900 px-3 py-4">
        <div className="flex gap-1">
          {modalities.map((item) => (
            <button
              key={item}
              onClick={() => setActiveModality(item)}
              className={`rounded px-3 py-1 text-base font-medium transition ${
                item === activeModality
                  ? "bg-blue-600 text-white"
                  : "bg-slate-800 text-slate-300 hover:bg-slate-700"
              }`}
            >
              {item}
            </button>
          ))}
        </div>

        <div className="flex items-center gap-2">
          <Tag color="default" className="m-0 px-3 py-1 text-sm">
            Patient: {patientId}
          </Tag>

          <Tag color="blue" className="m-0 px-4 py-1 text-base">
            Slice{" "}
            {currentImage?.sliceIndex ??
              (filteredImages.length > 0 ? currentImageIndex + 1 : 14)}{" "}
            / {currentImage?.totalSlices ?? (filteredImages.length || 72)}
          </Tag>
        </div>
      </div>

      <div className="grid flex-1 grid-cols-[40px_1fr] bg-black">
        {/* 左侧工具栏 */}
        <div className="flex flex-col items-center gap-3 border-r border-slate-800 bg-slate-950 py-4 text-slate-400">
          <ScanOutlined />
          <PlusCircleOutlined />
          <ReloadOutlined />
          <InfoCircleOutlined />
          <MedicineBoxOutlined />
        </div>

        {/* 主影像区域 */}
        <div className="relative min-h-[310px] overflow-hidden bg-black">
          <div className="flex items-center justify-between px-6 pt-4 pb-6 text-xs text-slate-300">
            <span>{currentImage?.sequence || "T2WI axial"}</span>

            <span className="text-slate-400">
              {currentPatient.name || "未选择病人"} /{" "}
              {currentPatient.age ?? "-"}岁 /{" "}
              {currentPatient.sex || currentPatient.gender || "-"}
            </span>
          </div>

          <div className="relative h-[65%] w-full overflow-hidden bg-black">
            {loading ? (
              <div className="flex h-full w-full items-center justify-center">
                <Spin tip="正在加载影像..." />
              </div>
            ) : errorMsg ? (
              <div className="flex h-full w-full items-center justify-center px-6 text-center text-sm text-red-400">
                {errorMsg}
              </div>
            ) : (
              <img
                src={currentImage?.url || "/img/zhanwei2.png"}
                alt="MRI image"
                className="absolute inset-0 h-full w-full object-contain opacity-90"
              />
            )}
          </div>

          {/* 只有选择病人后才显示 AI 标注 */}
          {/* {hasValidPatient && (
            <>
              <div className="absolute left-[28%] top-[34%] h-9 w-9 rounded-full border-2 border-orange-400 bg-orange-400/10 shadow-[0_0_18px_rgba(251,146,60,0.8)]">
                <span className="absolute -top-9 left-1/2 w-28 -translate-x-1/2 text-center text-[11px] font-semibold text-orange-300">
                  Suspicious Lymph Node
                </span>
              </div>

              <div className="absolute right-[18%] top-[20%] h-28 w-20 rounded-[50%] border-2 border-green-400 bg-green-400/10 shadow-[0_0_20px_rgba(74,222,128,0.7)]">
                <span className="absolute -top-5 left-1/2 w-24 -translate-x-1/2 text-center text-[11px] font-semibold text-green-300">
                  Parametrial interface
                </span>
              </div>
            </>
          )} */}

          {/* 底部切片缩略图 */}
          <div className="absolute bottom-4 left-5 right-5 grid grid-cols-8 gap-2">
            {(filteredImages.length > 0
              ? filteredImages.slice(0, 8)
              : Array.from({ length: 8 })
            ).map((item, index) => {
              const imageItem = item as PatientImage;

              return (
                <button
                  key={imageItem?.id || index}
                  onClick={() => setCurrentImageIndex(index)}
                  className={`h-12 overflow-hidden rounded border bg-[radial-gradient(circle,rgba(180,180,180,0.5),rgba(30,30,30,0.95))] ${
                    index === currentImageIndex
                      ? "border-blue-400 shadow-[0_0_10px_rgba(96,165,250,0.9)]"
                      : "border-slate-700"
                  }`}
                >
                  {imageItem?.url && (
                    <img
                      src={imageItem.url}
                      alt={`slice-${index + 1}`}
                      className="h-full w-full object-cover opacity-80"
                    />
                  )}
                </button>
              );
            })}
          </div>
        </div>
      </div>

      {/* 底部控制栏 */}
      <div className="flex items-center justify-between border-t border-slate-800 bg-slate-900 px-4 py-2 text-xs text-slate-300">
        <Space>
          <span>Window/Level</span>
          <Button size="small" type="text" className="text-slate-300">
            Auto
          </Button>
        </Space>

        <Space>
          {/* <label className="flex items-center gap-1">
            <input type="checkbox" defaultChecked />
            AI Overlay
          </label>

          <label className="flex items-center gap-1">
            <input type="checkbox" defaultChecked />
            Show Annotations
          </label> */}
        </Space>
      </div>
    </Card>
  );
}