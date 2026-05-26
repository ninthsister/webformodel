"use client";

import { useEffect, useMemo, useState } from "react";
import {
  InfoCircleOutlined,
  MedicineBoxOutlined,
  PlusCircleOutlined,
  ReloadOutlined,
  ScanOutlined,
  LeftOutlined,
  RightOutlined,
} from "@ant-design/icons";
import { Button, Card, Space, Spin, Tag } from "antd";
import type { Patient } from "@/app/main/page";
import type { Language } from "@/components/i18n";
import { buildApiUrl, getLanguageHeaders, zhEn } from "@/components/i18n";

type ViewerPatient = Patient & {
  mriSequences?: string[];
};

type MRIViewerProps = {
  currentPatient?: ViewerPatient;
  language?: Language;
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

const defaultPatient: ViewerPatient = {
  id: "??????",
  name: "未选择病人",
  age: 0,
  gender: "未知",
  stage: "未知",
  date: "未知",
  modalities: [],
  mriSequences: [],
};

const DEFAULT_MODALITIES = ["MRI", "PET", "CT", "PET/CT"];
const DEFAULT_MRI_SEQUENCES = ["T1", "T1CE", "T2"];
const THUMBNAIL_PAGE_SIZE = 8;

function normalizeText(value?: string) {
  return (value || "").trim().toLowerCase();
}

export default function MRIViewer({
  currentPatient = defaultPatient,
  language = "zh",
}: MRIViewerProps) {
  const [images, setImages] = useState<PatientImage[]>([]);
  const [currentImageIndex, setCurrentImageIndex] = useState(0);
  const [activeModality, setActiveModality] = useState("MRI");
  const [activeMriSequence, setActiveMriSequence] = useState("T1");
  const [loading, setLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState("");
  const [thumbnailStartIndex, setThumbnailStartIndex] = useState(0);

  const patientId = currentPatient?.id || "??????";
  const hasValidPatient = patientId !== "??????" && patientId.trim() !== "";

  const modalities = useMemo(() => {
    if (currentPatient?.modalities && currentPatient.modalities.length > 0) {
      return currentPatient.modalities;
    }

    return DEFAULT_MODALITIES;
  }, [currentPatient]);

  const mriSequences = useMemo(() => {
    if (
      currentPatient?.mriSequences &&
      currentPatient.mriSequences.length > 0
    ) {
      return currentPatient.mriSequences;
    }

    return DEFAULT_MRI_SEQUENCES;
  }, [currentPatient]);

  const isMRISelected = normalizeText(activeModality) === "mri";

  useEffect(() => {
    const firstModality =
      currentPatient?.modalities && currentPatient.modalities.length > 0
        ? currentPatient.modalities[0]
        : DEFAULT_MODALITIES[0];

    const firstMriSequence =
      currentPatient?.mriSequences && currentPatient.mriSequences.length > 0
        ? currentPatient.mriSequences[0]
        : DEFAULT_MRI_SEQUENCES[0];

    setActiveModality(firstModality);
    setActiveMriSequence(firstMriSequence);
    setCurrentImageIndex(0);
    setThumbnailStartIndex(0);
  }, [
    currentPatient?.id,
    currentPatient?.modalities,
    currentPatient?.mriSequences,
  ]);

  const filteredImages = useMemo(() => {
    if (images.length === 0) {
      return [];
    }

    const modalityFiltered = images.filter((item) => {
      if (!item.modality) return true;
      return normalizeText(item.modality) === normalizeText(activeModality);
    });

    if (!isMRISelected) {
      return modalityFiltered.length > 0 ? modalityFiltered : images;
    }

    const sequenceFiltered = modalityFiltered.filter((item) => {
      if (!item.sequence) return true;
      return normalizeText(item.sequence) === normalizeText(activeMriSequence);
    });

    if (sequenceFiltered.length > 0) {
      return sequenceFiltered;
    }

    return modalityFiltered.length > 0 ? modalityFiltered : images;
  }, [images, activeModality, activeMriSequence, isMRISelected]);

  const currentImage = filteredImages[currentImageIndex];
  const totalFilteredSlices = filteredImages.length;

  const maxThumbnailStartIndex = Math.max(
    0,
    totalFilteredSlices - THUMBNAIL_PAGE_SIZE
  );

  const visibleThumbnails = useMemo(() => {
    if (filteredImages.length === 0) {
      return [];
    }

    return filteredImages.slice(
      thumbnailStartIndex,
      thumbnailStartIndex + THUMBNAIL_PAGE_SIZE
    );
  }, [filteredImages, thumbnailStartIndex]);

  const canScrollThumbnailsLeft = thumbnailStartIndex > 0;

  const canScrollThumbnailsRight =
    thumbnailStartIndex + THUMBNAIL_PAGE_SIZE < totalFilteredSlices;

  const scrollThumbnailsLeft = () => {
    setThumbnailStartIndex((prev) =>
      Math.max(0, prev - THUMBNAIL_PAGE_SIZE)
    );
  };

  const scrollThumbnailsRight = () => {
    setThumbnailStartIndex((prev) =>
      Math.min(maxThumbnailStartIndex, prev + THUMBNAIL_PAGE_SIZE)
    );
  };

  const selectSlice = (absoluteIndex: number) => {
    setCurrentImageIndex(absoluteIndex);
  };

  useEffect(() => {
    if (!hasValidPatient) {
      setImages([]);
      setCurrentImageIndex(0);
      setThumbnailStartIndex(0);
      setErrorMsg("");
      return;
    }

    const controller = new AbortController();

    const fetchPatientImages = async () => {
      try {
        setLoading(true);
        setErrorMsg("");
        setCurrentImageIndex(0);
        setThumbnailStartIndex(0);

        const res = await fetch(
          buildApiUrl(
            `/api/patient/${encodeURIComponent(
              patientId
            )}/images`,
            language
          ),
          {
            method: "GET",
            headers: getLanguageHeaders(language),
            signal: controller.signal,
          }
        );

        if (!res.ok) {
          throw new Error(
            `${zhEn(language, "请求失败", "Request failed")}: ${res.status}`
          );
        }

        const data: PatientImageResponse = await res.json();
        setImages(data.images || []);
      } catch (error) {
        if (error instanceof DOMException && error.name === "AbortError") {
          return;
        }

        console.error(error);
        setImages([]);
        setErrorMsg(
          zhEn(
            language,
            "影像数据加载失败，请检查后台接口或病人 ID。",
            "Failed to load images. Please check the backend API or patient ID."
          )
        );
      } finally {
        setLoading(false);
      }
    };

    fetchPatientImages();

    return () => {
      controller.abort();
    };
  }, [patientId, hasValidPatient, language]);

  useEffect(() => {
    setCurrentImageIndex(0);
    setThumbnailStartIndex(0);
  }, [activeModality]);

  useEffect(() => {
    setCurrentImageIndex(0);
    setThumbnailStartIndex(0);
  }, [activeMriSequence]);

  useEffect(() => {
    if (!isMRISelected) return;
    if (mriSequences.length === 0) return;

    const exists = mriSequences.some(
      (item) => normalizeText(item) === normalizeText(activeMriSequence)
    );

    if (!exists) {
      setActiveMriSequence(mriSequences[0]);
    }
  }, [isMRISelected, mriSequences, activeMriSequence]);

  useEffect(() => {
    if (filteredImages.length === 0) {
      setCurrentImageIndex(0);
      setThumbnailStartIndex(0);
      return;
    }

    if (currentImageIndex >= filteredImages.length) {
      setCurrentImageIndex(0);
    }

    if (thumbnailStartIndex > maxThumbnailStartIndex) {
      setThumbnailStartIndex(maxThumbnailStartIndex);
    }
  }, [
    filteredImages.length,
    currentImageIndex,
    thumbnailStartIndex,
    maxThumbnailStartIndex,
  ]);

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
      <div
        className="border-b border-slate-700 bg-slate-900 px-4 pt-4"
        style={{
          paddingBottom: isMRISelected ? 12 : 14,
        }}
      >
        <div className="flex items-center justify-between">
          <div className="flex flex-wrap gap-2">
            {modalities.map((item) => (
              <button
                key={item}
                onClick={() => setActiveModality(item)}
                className={`rounded-md px-4 py-2.5 text-base font-semibold leading-none transition ${
                  normalizeText(item) === normalizeText(activeModality)
                    ? "bg-blue-600 text-white shadow-sm"
                    : "bg-slate-800 text-slate-300 hover:bg-slate-700"
                }`}
              >
                {item}
              </button>
            ))}
          </div>

          <div className="flex items-center gap-2">
            <Tag color="default" className="m-0 px-3 py-1 text-sm">
              {zhEn(language, "病人", "Patient")}: {patientId}
            </Tag>

            <Tag color="blue" className="m-0 px-4 py-1 text-sm">
              {zhEn(language, "切片", "Slice")}{" "}
              {currentImage?.sliceIndex ??
                (filteredImages.length > 0 ? currentImageIndex + 1 : 0)}{" "}
              / {currentImage?.totalSlices ?? filteredImages.length}
            </Tag>
          </div>
        </div>

        {/* MRI 子序列切换栏 */}
        {isMRISelected && mriSequences.length > 0 && (
          <div className="mt-3 flex items-center gap-2">
            <span className="text-sm text-slate-400">
              {zhEn(language, "MRI 子序列", "MRI Sequence")}
            </span>

            <div className="flex flex-wrap gap-2">
              {mriSequences.map((item) => (
                <button
                  key={item}
                  onClick={() => setActiveMriSequence(item)}
                  className={`rounded-md px-4 py-2.5 text-sm font-semibold leading-none transition ${
                    normalizeText(item) === normalizeText(activeMriSequence)
                      ? "bg-cyan-600 text-white shadow-sm"
                      : "bg-slate-800 text-slate-300 hover:bg-slate-700"
                  }`}
                >
                  {item}
                </button>
              ))}
            </div>
          </div>
        )}
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
            <span>
              {isMRISelected
                ? currentImage?.sequence || activeMriSequence
                : currentImage?.sequence || ""}
            </span>

            <span className="text-slate-400">
              {currentPatient.name ||
                zhEn(language, "未选择病人", "No patient selected")}{" "}
              / {currentPatient.age ?? "-"}
              {zhEn(language, "岁", " years")} /{" "}
              {currentPatient.gender || "-"}
            </span>
          </div>

          <div className="relative h-[65%] w-full overflow-hidden bg-black">
            {loading ? (
              <div className="flex h-full w-full items-center justify-center">
                <Spin
                  tip={zhEn(
                    language,
                    "正在加载影像...",
                    "Loading images..."
                  )}
                />
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

          {/* 底部切片缩略图 */}
          <div className="absolute bottom-4 left-5 right-5">
            <div className="mb-2 flex items-center justify-between text-[11px] text-slate-400">
              <span>
                {zhEn(language, "切片缩略图", "Slice thumbnails")}{" "}
                {filteredImages.length > 0
                  ? `${thumbnailStartIndex + 1}-${Math.min(
                      thumbnailStartIndex + THUMBNAIL_PAGE_SIZE,
                      filteredImages.length
                    )} / ${filteredImages.length}`
                  : "0 / 0"}
              </span>

              <span>
                {isMRISelected
                  ? `${activeModality} / ${activeMriSequence}`
                  : activeModality}
              </span>
            </div>

            <div className="grid grid-cols-[32px_1fr_32px] items-center gap-2">
              <button
                type="button"
                onClick={scrollThumbnailsLeft}
                disabled={!canScrollThumbnailsLeft}
                className={`flex h-12 items-center justify-center rounded border text-xs transition ${
                  canScrollThumbnailsLeft
                    ? "border-slate-600 bg-slate-900 text-slate-200 hover:border-blue-400 hover:text-blue-300"
                    : "cursor-not-allowed border-slate-800 bg-slate-950 text-slate-700"
                }`}
              >
                <LeftOutlined />
              </button>

              <div className="grid grid-cols-8 gap-2">
                {(visibleThumbnails.length > 0
                  ? visibleThumbnails
                  : Array.from({ length: THUMBNAIL_PAGE_SIZE })
                ).map((item, index) => {
                  const imageItem = item as PatientImage;
                  const absoluteIndex = thumbnailStartIndex + index;
                  const isActive = absoluteIndex === currentImageIndex;

                  return (
                    <button
                      key={imageItem?.id || absoluteIndex}
                      type="button"
                      onClick={() => {
                        if (imageItem?.url) {
                          selectSlice(absoluteIndex);
                        }
                      }}
                      className={`relative h-12 overflow-hidden rounded border bg-[radial-gradient(circle,rgba(180,180,180,0.5),rgba(30,30,30,0.95))] transition ${
                        isActive
                          ? "border-blue-400 shadow-[0_0_10px_rgba(96,165,250,0.9)]"
                          : "border-slate-700 hover:border-slate-400"
                      }`}
                    >
                      {imageItem?.url && (
                        <>
                          <img
                            src={imageItem.url}
                            alt={`slice-${absoluteIndex + 1}`}
                            className="h-full w-full object-cover opacity-80"
                          />

                          <span className="absolute bottom-0 right-0 rounded-tl bg-black/70 px-1 text-[10px] text-slate-200">
                            {imageItem.sliceIndex ?? absoluteIndex + 1}
                          </span>
                        </>
                      )}
                    </button>
                  );
                })}
              </div>

              <button
                type="button"
                onClick={scrollThumbnailsRight}
                disabled={!canScrollThumbnailsRight}
                className={`flex h-12 items-center justify-center rounded border text-xs transition ${
                  canScrollThumbnailsRight
                    ? "border-slate-600 bg-slate-900 text-slate-200 hover:border-blue-400 hover:text-blue-300"
                    : "cursor-not-allowed border-slate-800 bg-slate-950 text-slate-700"
                }`}
              >
                <RightOutlined />
              </button>
            </div>
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

        <Space />
      </div>
    </Card>
  );
}