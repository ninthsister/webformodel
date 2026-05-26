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
安装以来
```bash
cd model-demo-web
npm install
```

启动前端：

```bash
npm run dev
```
---

## 4. 页面组件说明

当前 `/main` 页面建议只负责整体布局，具体功能拆分到组件中。

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

## 5. 后端环境准备

推荐使用 conda：

```bash
conda create -n web_backend python=3.10 -y
conda activate web_backend
```

如果后续要直接接入已有 PyTorch / nnUNet 模型，也可以使用已有模型环境。

---

## 6. 安装后端依赖

```bash
pip install -r requirements.txt
```

启动后端：
```bash
cd model-demo-backend
uvicorn main_new:app --reload --host 0.0.0.0 --port 8000
```