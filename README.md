# 医学诊疗系统前后端项目说明(由GPT生成)

本项目是一个用于医学 AI 模型展示与诊疗辅助分析的 Web 系统。

当前项目采用前后端分离结构：

```txt
前端：Next.js + React + TypeScript + Tailwind CSS + Ant Design
后端：Python + FastAPI + uvicorn
模型：PyTorch / nnUNet / 自定义医学影像模型
```

系统主要用于展示：

```txt
1. 病人基础信息
2. MRI / CT / PET-CT 等模态状态
3. 医学影像查看器
4. PLNM / PMI 风险评估
5. 证据充分性检查
6. AI 生成报告草稿
7. 关键影像证据
8. 医生反馈
9. 报告导出与补充检查请求
```

---

## 1. 项目整体结构

推荐项目目录如下：

```txt
model-demo-web          # 前端项目
└── model-demo-backend      # 后端项目
```

---

## 2. 前端环境准备

### 2.1 安装 Node.js

推荐使用 `nvm` 安装 Node.js，适合 Linux 服务器环境。

```bash
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.4/install.sh | bash
```

加载 nvm：

```bash
source ~/.bashrc
```

如果使用 zsh：

```bash
source ~/.zshrc
```

检查 nvm 是否安装成功：

```bash
nvm --version
```

安装 Node.js LTS 版本：

```bash
nvm install --lts
nvm use --lts
nvm alias default node
```

检查 Node.js 和 npm：

```bash
node -v
npm -v
```

如果能够显示版本号，说明安装成功。

---

## 3. 前端项目
进入项目：

```bash
cd model-demo-web
```

启动前端：

```bash
npm run dev
```

如果在 Linux 服务器上运行，并希望外部浏览器访问：

```bash
npm run dev -- -H 0.0.0.0
```

访问：

```txt
http://服务器IP:3000
```

本机访问：

```txt
http://127.0.0.1:3000
```

---

## 4. 安装前端常用依赖

进入前端项目目录：

```bash
cd model-demo-web
```

安装 Ant Design：

```bash
npm install antd @ant-design/nextjs-registry
```

安装图标库：

```bash
npm install @ant-design/icons
```

安装请求库：

```bash
npm install axios
```

安装图表库：

```bash
npm install echarts echarts-for-react
```

当前前端主要依赖说明：

```txt
antd                         UI 组件库
@ant-design/nextjs-registry  Ant Design 适配 Next.js App Router
@ant-design/icons            Ant Design 图标库
axios                        前端请求后端接口
echarts                      图表库
echarts-for-react            React 中使用 ECharts
```

如果后续需要模型结构流程图，可以安装：

```bash
npm install reactflow
```

如果后续需要 3D 展示，可以安装：

```bash
npm install three @react-three/fiber @react-three/drei
```

---

## 5. 配置 Ant Design

打开：

```txt
src/app/layout.tsx
```

修改为：

```tsx
import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import { AntdRegistry } from "@ant-design/nextjs-registry";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "医学诊疗系统",
  description: "Medical AI Diagnosis System",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="zh-CN"
      className={`${geistSans.variable} ${geistMono.variable} h-full antialiased`}
    >
      <body className="min-h-full flex flex-col">
        <AntdRegistry>{children}</AntdRegistry>
      </body>
    </html>
  );
}
```
---

## 7. 页面组件说明

当前 `/test` 页面建议只负责整体布局，具体功能拆分到组件中。

```txt
顶部病人信息栏              PatientHeader
左侧影像查看器              MRIViewer
中间风险评估结果            AssessmentPanel
右侧证据状态与推理说明       ReasoningPanel
左下报告草稿 + 关键证据      ReportEvidencePanel
右下医生反馈 + 操作按钮      FeedbackActionPanel
```

页面整体布局示意：

```txt
TestPage
├── 顶部标题栏
├── PatientHeader
├── 第一行主体区域
│   ├── MRIViewer
│   ├── AssessmentPanel
│   └── ReasoningPanel
└── 第二行结果与操作区域
    ├── ReportEvidencePanel
    └── FeedbackActionPanel
```

---

## 8. 后端环境准备

### 8.1 创建 Python 环境

推荐使用 conda：

```bash
conda create -n medical_backend python=3.10 -y
conda activate medical_backend
```

如果后续要直接接入已有 PyTorch / nnUNet 模型，也可以使用已有模型环境。

---

## 9. 安装后端依赖

基础后端依赖：

```bash
pip install fastapi uvicorn python-multipart pillow numpy
```

如果需要 PyTorch 推理：

```bash
pip install torch torchvision
```

如果需要读取医学影像文件：

```bash
pip install nibabel SimpleITK pydicom opencv-python
```

如果需要读取 `.h5` 文件：

```bash
pip install h5py
```

最小依赖：

```txt
fastapi
uvicorn
python-multipart
pillow
numpy
```

完整一点的依赖：

```txt
fastapi
uvicorn
python-multipart
pillow
numpy
torch
torchvision
opencv-python
pydicom
SimpleITK
nibabel
h5py
```

---

## 11. 后端 requirements.txt

创建：

```txt
requirements.txt
```

第一版可以写：

```txt
fastapi
uvicorn
python-multipart
pillow
numpy
```

如果要接模型，扩展为：

```txt
fastapi
uvicorn
python-multipart
pillow
numpy
torch
torchvision
opencv-python
pydicom
SimpleITK
nibabel
h5py
```

安装：

```bash
pip install -r requirements.txt
```