# History-RAG Modern SaaS Web Frontend

This directory contains the production-grade **React 19 + TypeScript + Vite + Tailwind CSS v4** frontend for **History-RAG — History-Aware Repository Intelligence and AI-Enhanced DevOps Platform**.

---

## 📖 Complete Technical Documentation

For an exhaustive, minute-by-minute breakdown of the frontend architecture, component library, view specifications, API contracts, defensive error handling, and build systems, please refer to the comprehensive guide in the project root:

👉 **[`../FRONTEND_DOCUMENTATION.md`](../FRONTEND_DOCUMENTATION.md)**

---

## 🚀 Quick Start

### 1. Install Dependencies
```bash
npm install
```

### 2. Start Local Development Server
```bash
npm run dev -- --host 0.0.0.0 --port 3000
```
Open **`http://localhost:3000`** in your browser. (API requests are automatically proxied to the FastAPI backend running on port 8000).

### 3. Build for Production
```bash
npm run build
```
Generates optimized static assets in `dist/`. These assets are automatically mounted and served by FastAPI at **`http://localhost:8000/dashboard/`** (or via redirect at **`http://localhost:8000/app`**).

### 4. Code Quality & Linting
```bash
npx oxlint
```

---

## 📁 Directory Structure

```
frontend/
├── public/                 # Static brand SVGs and favicons
├── src/
│   ├── assets/             # Vector icons and images
│   ├── components/
│   │   ├── layout/         # Structural layout components
│   │   │   ├── Header.tsx  # Dynamic breadcrumbs, global repo selector & operator profile
│   │   │   └── Sidebar.tsx # Linear-style collapsible navigation drawer
│   │   └── ui/             # Reusable SaaS design primitives
│   │       ├── Badge.tsx   # Color-coded status & severity pills
│   │       ├── Button.tsx  # Accessible action buttons with spinner states
│   │       ├── Card.tsx    # Standardized card surfaces and headers
│   │       ├── EmptyState.tsx # Empty collection placeholders
│   │       └── ErrorBanner.tsx# Alert banners with retry callbacks
│   ├── services/
│   │   └── api.ts          # Stream-safe HTTP client & typed backend endpoints
│   ├── types/
│   │   └── api.ts          # Full TypeScript contracts matching backend models
│   ├── views/              # The 7 core production SaaS views
│   │   ├── OverviewView.tsx       # Landing KPIs, repo profile & deployments
│   │   ├── RepositoriesView.tsx   # GitHub cloning & ZIP drag-and-drop ingestion
│   │   ├── ChangeAnalysisView.tsx # Intent/Diff blast radius & test recommender
│   │   ├── ExplorerView.tsx       # Dual-pane repository code & syntax viewer
│   │   ├── CicdView.tsx           # 1-Click GitHub Actions workflow onboarding
│   │   ├── PolicyGateView.tsx     # Merge governance & automated rollback engine
│   │   └── ObservabilityView.tsx  # Real-time Prometheus metrics & latency quantiles
│   ├── App.tsx             # Root orchestrator, global state & health polling
│   ├── index.css           # Tailwind CSS v4 design tokens and styles
│   └── main.tsx            # React 19 application entry point
├── package.json            # Scripts and dependencies
├── tsconfig.json           # TypeScript configuration
└── vite.config.ts          # Vite build & proxy configuration
```

---
*For full details, see [`../FRONTEND_DOCUMENTATION.md`](../FRONTEND_DOCUMENTATION.md).*
