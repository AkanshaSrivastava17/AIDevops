# History-RAG Frontend Web Application — Comprehensive Architecture & Implementation Specification

> **Platform**: History-RAG — History-Aware Repository Intelligence and AI-Enhanced DevOps Platform  
> **Technology Stack**: React 19, TypeScript 5.8, Vite 6, Tailwind CSS v4, Lucide Icons  
> **Design Philosophy**: Developer-First SaaS inspired by Linear, Vercel, Stripe, and GitHub  
> **Document Scope**: Exhaustive implementation details across architecture, components, views, API contracts, state management, and deployment.

---

## Table of Contents

1. [Executive Summary & Architectural Philosophy](#1-executive-summary--architectural-philosophy)
2. [Design System & Visual Language](#2-design-system--visual-language)
3. [Core Application Layout & Navigation Infrastructure](#3-core-application-layout--navigation-infrastructure)
4. [Reusable SaaS UI Component Library](#4-reusable-saas-ui-component-library)
5. [In-Depth View-by-View Implementation Specification](#5-in-depth-view-by-view-implementation-specification)
   - [5.1 Overview Dashboard (`OverviewView.tsx`)](#51-overview-dashboard-overviewviewtsx)
   - [5.2 Repository Manager (`RepositoriesView.tsx`)](#52-repository-manager-repositoriesviewtsx)
   - [5.3 Change Impact Analysis (`ChangeAnalysisView.tsx`)](#53-change-impact-analysis-changeanalysisviewtsx)
   - [5.4 Repository Code Explorer (`ExplorerView.tsx`)](#54-repository-code-explorer-explorerviewtsx)
   - [5.5 CI/CD Integration (`CicdView.tsx`)](#55-cicd-integration-cicdviewtsx)
   - [5.6 Policy Gate & Rollback Manager (`PolicyGateView.tsx`)](#56-policy-gate--rollback-manager-policygateviewtsx)
   - [5.7 Observability & Telemetry (`ObservabilityView.tsx`)](#57-observability--telemetry-observabilityviewtsx)
6. [API Integration Layer & Data Contracts](#6-api-integration-layer--data-contracts)
7. [Defensive Engineering & Error Resiliency](#7-defensive-engineering--error-resiliency)
8. [Build Pipeline & Production Deployment](#8-build-pipeline--production-deployment)
9. [Developer Operations & Execution Guide](#9-developer-operations--execution-guide)

---

## 1. Executive Summary & Architectural Philosophy

### 1.1 Purpose & Role of the Web Application
The **History-RAG Frontend Web Application** serves as the primary developer interface for the **History-Aware Repository Intelligence Platform**. The platform integrates:
- Universal **Tree-Sitter AST syntax trees** across polyglot codebases (Python, JavaScript, TypeScript, Go, Java, Rust, C, C++).
- Grounded **historical Git commit, issue, and Pull Request memory** indexed in ChromaDB vector stores and SQLite structured metadata.
- Deterministic **Evidence Scoring Engine** and **Test Recommender**.
- Autonomous **CI/CD Policy Gates** and zero-downtime **Rollback Engines**.

The frontend exposes these complex capabilities through an intuitive, production-grade SaaS interface that requires zero onboarding friction.

### 1.2 Core Architectural Principles
1. **Zero-Mock Policy (Strict API Integrity)**: The application communicates strictly with real backend endpoints (`GET /repositories`, `POST /analyze-change`, `POST /evaluate-gate`, `GET /metrics`). Fabricated fallback mock data is strictly eliminated. If an endpoint encounters an error or goes offline, real error banners with retry triggers are rendered.
2. **Deterministic UI State**: The entire interface is driven by a single active repository context (`activeRepoId`), propagated globally from the top-level application orchestrator down to every view.
3. **Restrained Visual Aesthetics**: Heavy glowing neon gradients, excessive glassmorphism, and cartoonish emoji icons are banned. The UI defaults to a crisp, high-contrast light theme engineered for all-day software engineering and DevOps operations.
4. **Coexistence with Classic Interfaces**: The modern React SaaS application seamlessly coexists with the classic Streamlit workbench (`http://localhost:8501`) and FastAPI backend documentation (`http://localhost:8000/docs`).

---

## 2. Design System & Visual Language

The design system establishes a uniform visual rhythm across all pages, inspired by the clean precision of **Linear**, the developer aesthetic of **Vercel**, and the data clarity of **Stripe**.

### 2.1 Color Palette Specifications

| Role | Token / Name | Hex Code | Purpose & Usage |
| :--- | :--- | :--- | :--- |
| **Page Canvas** | Soft Neutral Background | `#F8FAFC` (Slate 50) | Base canvas background for the entire application. |
| **Card / Surface** | Pure White Surface | `#FFFFFF` | Container backgrounds, tables, modals, input elements. |
| **Borders** | Subtle Gray Border | `#E2E8F0` (Slate 200) | 1px clean separation borders between cards, tables, and headers. |
| **Primary Text** | Deep Slate | `#0F172A` (Slate 900) | Headings, titles, metric values, table text. |
| **Secondary Text** | Muted Slate | `#64748B` (Slate 500) | Subtitles, labels, metadata timestamps, table headers. |
| **Primary Brand Accent** | Sophisticated Indigo | `#4F46E5` (Indigo 600) | Primary CTA buttons, active sidebar items, key highlight badges. |
| **Brand Accent Hover** | Deep Indigo | `#4338CA` (Indigo 700) | Hover state for primary interactive elements. |
| **Brand Accent Light** | Indigo Tint | `#EEF2FF` (Indigo 50) | Active pill background, brand badge backgrounds. |
| **Success / Safe** | Emerald Green | `#10B981` (Emerald 500) | Approved policy gates, low risk scores, active health beacons. |
| **Warning / Caution** | Amber Yellow | `#F59E0B` (Amber 500) | Medium risk scores, AST warnings, test review suggestions. |
| **Danger / High Risk** | Rose Red | `#EF4444` (Rose 500) | Blocked gates, high risk scores, network failure banners. |

### 2.2 Typography & Iconography
- **Body & Headings**: Inter / System Sans-Serif font stack with strict font weights:
  - `font-normal` (400) for body descriptions.
  - `font-medium` (500) for input labels, table cell text, and secondary metrics.
  - `font-semibold` (600) for section titles, card headers, and button text.
  - `font-bold` (700) for page headings, KPI counters, and status badges.
- **Code & AST Artifacts**: `font-mono` (JetBrains Mono, Fira Code, Menlo) with exact line heights (`leading-relaxed`) for Git diffs, unified patches, commit SHAs, container tags, and code blocks.
- **Icons**: 100% **Lucide React** SVG icons. Every icon is strictly sized (`w-3.5 h-3.5`, `w-4 h-4`, `w-5 h-5`) and colored contextually (`text-indigo-600`, `text-emerald-500`, `text-slate-400`).

---

## 3. Core Application Layout & Navigation Infrastructure

The layout follows a classic two-pane SaaS dashboard pattern: a collapsible left sidebar, a compact top header, and a scrollable main content viewport.

```
+-------------------------------------------------------------------------------+
| HISTORY-RAG | Active Repo: Pycalculator | Breadcrumbs | Backend: Online (200) |
+-------------+-----------------------------------------------------------------+
| [WORKSPACE] |                                                                 |
|  Overview   |                                                                 |
|  Repos      |                  ACTIVE MAIN VIEW CONTAINER                     |
|  Analysis   |                 (Overview / Repositories /                      |
| [INTEL]     |            Change Impact / Explorer / CI/CD /                   |
|  Explorer   |             Policy Gate / Observability)                        |
| [DEVOPS]    |                                                                 |
|  CI/CD      |                                                                 |
|  Gate       |                                                                 |
| [MONITOR]   |                                                                 |
|  Metrics    |                                                                 |
|             |                                                                 |
|  API Status |                                                                 |
+-------------+-----------------------------------------------------------------+
```

### 3.1 Collapsible Sidebar (`frontend/src/components/layout/Sidebar.tsx`)
- **Brand Identity**: Displays the History-RAG brand mark (`GitBranch` inside an indigo container), the platform title **"History-RAG"**, and the enterprise subtitle **"Repository Intelligence Platform"**.
- **Collapsible State**: Toggled via a collapse chevron at the bottom of the sidebar. When collapsed:
  - The sidebar shrinks smoothly from `w-64` to `w-18`.
  - Section titles and text labels fade out using CSS opacity and width transitions.
  - Floating tooltip pills appear on hover over each navigation item.
- **Categorized Navigation**:
  1. **WORKSPACE**:
     - `overview` &rarr; Overview Dashboard (`LayoutDashboard` icon).
     - `repositories` &rarr; Repository Manager (`FolderGit2` icon).
     - `analysis` &rarr; Change Impact Analysis (`GitCompare` icon).
  2. **INTELLIGENCE**:
     - `explorer` &rarr; Repository Explorer (`FileCode2` icon).
  3. **DEVOPS**:
     - `cicd` &rarr; CI/CD Integration (`GitPullRequest` icon).
     - `gate` &rarr; Policy Gate & Deployments (`ShieldCheck` icon).
  4. **MONITORING**:
     - `observability` &rarr; Observability & Telemetry (`Activity` icon).
- **Backend Connection Beacon**: Positioned at the footer of the sidebar. Displays a pulsing emerald dot (`bg-emerald-500`) when connected to the FastAPI backend, or a pulsing rose dot (`bg-rose-500`) with `"Backend Offline"` if the server is unreachable.

### 3.2 Contextual Top Header (`frontend/src/components/layout/Header.tsx`)
- **Dynamic Breadcrumb Engine**: Automatically parses the active `currentView` to display category and page breadcrumbs (e.g., `Workspace / Change Impact Analysis` or `DevOps / Policy Gate & Deployments`).
- **Global Repository Selector**: A styled HTML `<select>` dropdown populated from `GET /repositories`. Selecting a different repository immediately updates the global `activeRepoId` in `App.tsx`, triggering instant synchronization across all dependent views.
- **Operator Badge**: Displays the detected local Git operator (`AkanshaSrivastava17`) with a GitHub icon.
- **Streamlit Workbench Link**: An external navigation pill pointing directly to `http://localhost:8501`, ensuring seamless switching between the SaaS web app and the Python Streamlit analytics app.

### 3.3 Root Application Orchestrator (`frontend/src/App.tsx`)
- **Lifecycle Initialization**:
  On component mount (`useEffect`), `App.tsx` concurrently triggers:
  ```ts
  const [h, repos] = await Promise.all([
    fetchHealth().catch(() => null),
    fetchRepositories().catch(() => [] as RepositoryItem[]),
  ]);
  ```
  It validates backend reachability, sets `isOnline`, populates the repository catalog, and defaults the active repository to the first available repository (e.g., `pycalculator` or `netbox`).
- **Heartbeat Daemon**: An active interval executes `fetchHealth()` every 10 seconds, maintaining an accurate real-time indicator of backend health.
- **Repository Added Handler**: When a user clones a new repository or uploads a ZIP file in `RepositoriesView`, `handleRepoAdded(newRepo)` prepends the new repository to the global state and automatically sets it as the active repository.

---

## 4. Reusable SaaS UI Component Library

All primitive user interface components are encapsulated in `frontend/src/components/ui/` to guarantee visual consistency and maintainability.

### 4.1 Button (`Button.tsx`)
- **Props**: `variant` (`primary`, `secondary`, `outline`, `danger`, `ghost`), `size` (`sm`, `md`, `lg`), `loading` (`boolean`), `icon` (`ReactNode`), standard HTML button attributes.
- **Implementation Highlights**:
  - Encapsulates loading state using Lucide's `Loader2` with `animate-spin`.
  - Automatically disables interactions (`disabled={disabled || loading}`) during asynchronous operations.
  - Features an explicit `type={type}` (defaulting to `'button'`) while preserving direct `onClick` event propagation.
  - Active focus states use `focus-visible:outline-2 focus-visible:outline-offset-2`.

### 4.2 Card (`Card.tsx`)
- **Compound Structure**: Composed of `Card` (outer surface with subtle border `#E2E8F0` and `shadow-xs`), `CardHeader` (header bar with title, subtitle, and optional action buttons), and `CardContent` (padded body area).
- **Hoverable Prop**: When `hoverable=true`, applies smooth hover elevation: `hover:border-slate-300 hover:shadow-sm transition-all`.

### 4.3 Badge (`Badge.tsx`)
- **Variants**: `success` (emerald), `warning` (amber), `error` (rose), `info` (sky), `brand` (indigo), `neutral` (slate).
- **Dot Indicator**: The optional `dot={true}` prop injects a 6px status circle before the label, used for impact severity levels (`LOW`, `MEDIUM`, `HIGH`) and operational status.

### 4.4 ErrorBanner (`ErrorBanner.tsx`)
- Renders high-visibility error alerts with `AlertCircle`, dark red typography, an optional `onRetry` action button, and a dismiss button (`X`).
- Used to catch and display real backend exceptions without breaking the page layout.

### 4.5 EmptyState (`EmptyState.tsx`)
- Renders dashed-border containers with centered icons, descriptive titles, explanations, and optional call-to-action buttons for empty datasets (e.g., no repositories, no search results, no test recommendations).

---

## 5. In-Depth View-by-View Implementation Specification

### 5.1 Overview Dashboard (`OverviewView.tsx`)

#### Purpose
The primary landing dashboard displaying high-level repository intelligence metrics, the active repository's AST capability profile, quick-action navigation, and recent production deployments.

#### Data Fetching
- Calls `fetchRepositoryStatus(activeRepo.repository_id)` (`GET /repository-status`) to retrieve real document counts, discovered components, language, and analysis mode.
- Calls `fetchDeployments()` (`GET /devops/deployments`) to fetch the staging deployment audit trail.

#### UI Sections
1. **Welcome Banner**: Displays a personalized greeting ("Good morning / afternoon / evening") with the formatted current date and live platform readiness badge.
2. **KPI Metric Grid (4 Cards)**:
   - **Total Indexed Repositories**: Length of configured repository registry.
   - **Indexed Documents & Chunks**: Real document count from SQLite (`total_documents`).
   - **Discovered Components**: Count of AST-profiled components (`discovered_components.length`).
   - **Historical Commits & PRs**: Total Git commits and issue records indexed in repository memory.
3. **Active Repository Profile Card**:
   - Primary language badge.
   - Universal AST Engine tag (`Tree-Sitter universal AST`).
   - Analysis mode tag (`Enhanced History-RAG`).
   - Component tags: Interactive pills displaying each discovered component (`Calculator`, `IPAM`, `DCIM`, etc.).
4. **Quick Action Shortcuts**: One-click navigation cards to:
   - *Analyse Code Change* &rarr; navigates to `analysis`.
   - *Add / Ingest Repository* &rarr; navigates to `repositories`.
   - *Explore Repository Code* &rarr; navigates to `explorer`.
   - *Verify Policy Gate* &rarr; navigates to `gate`.
5. **Recent Production Deployments Table**: Chronological audit trail showing Deployment ID, Container Tag (`historyrag:v1.0.0-stable`), Target Environment (`qa`), Health Status (`HEALTHY`), and Deployment Timestamp.

---

### 5.2 Repository Manager (`RepositoriesView.tsx`)

#### Purpose
Provides centralized repository onboarding and lifecycle management, allowing software engineers to connect remote GitHub repositories or upload local codebase ZIP archives.

#### Implementation Details
1. **Option 1: Connect via GitHub URL**:
   - Input for GitHub Repository URL (e.g., `https://github.com/Radhikag19/PyCalculator`).
   - Input for Branch Name (defaults to `main`).
   - Submits to `cloneRepository(url)` (`POST /index`).
   - Activates a loading spinner during clone and Tree-Sitter AST profiling.
   - On success, triggers `onRepoAdded` and automatically selects the newly cloned repository.
2. **Option 2: Upload Codebase Archive (.ZIP)**:
   - Drag-and-drop file dropzone accepting `.zip` archives up to 100MB.
   - File input fallback with file size and type validation.
   - Optional custom repository slug field.
   - Submits multipart form data to `uploadRepositoryZip(file, slug)` (`POST /upload-repository`).
   - Unpacks the archive on the backend, executes Tree-Sitter AST profiling, indexes vectors into ChromaDB, and inserts metadata into SQLite.
3. **Indexed Repositories Inventory Table**:
   - Real-time client-side search filter by repository name or language.
   - Columns: Repository Name, Source URL, Primary Language, Status (`Active` vs. `Indexed`), Action buttons (`Select Active`, `Open Explorer`, `Analyze Change`).
   - Visually highlights the active repository with an emerald active badge and bold typography.

---

### 5.3 Change Impact Analysis (`ChangeAnalysisView.tsx`)

#### Purpose
The platform's flagship feature. Predicts the blast radius of proposed code changes, ranks affected components, selects regression test suites, synthesizes candidate tests, and displays grounded historical evidence.

#### Input Modes
- **Plain English Intent**: Textarea where developers describe the planned scenario in natural language (e.g., *"In calculator.py, add a zero-division check to divide() to prevent crashes when denominator is 0."*).
- **Git Diff / Unified Patch**: Textarea accepting standard unified diff format (e.g., `diff --git a/calculator.py b/calculator.py ...`).

#### Controls & Parameters
- **System Mode Selector**:
  - `History-RAG`: Full hybrid mode combining historical commit co-changes, PR discussions, and Tree-Sitter AST call graphs.
  - `Semantic-only` (Code-RAG): Dense vector semantic search over current code and tests.
  - `History-RAG + Graph`: Multi-hop relationship paths across the repository knowledge graph.
  - `LLM-only`: Direct LLM reasoning baseline without retrieval.
- **Max Recommended Tests Input**: Number input (1 to 15) determining how many regression tests to rank.
- **Synthesize Candidate Tests Checkbox**: Toggles automated AI generation of new `pytest` test snippets.

#### Output & Results Presentation
1. **Executive Impact Summary (4 KPI Cards)**:
   - **Overall Severity**: Color-coded risk badge (`LOW`, `MEDIUM`, `HIGH`, `CRITICAL`).
   - **AI Confidence Score**: Confidence percentage computed by the Grounded LLM engine.
   - **Affected Components Count**: Number of components identified in the blast radius.
   - **Recommended Tests Count**: Number of regression test suites prioritized for execution.
2. **Table 1: Affected Components & Risk Breakdown**:
   - Component Name (monospace font).
   - Impact Score (numerical 0.00–1.00).
   - Severity Badge (LOW/MEDIUM/HIGH).
   - Reason / Heuristic: Detailed explanation from co-change correlation and AST import links.
3. **Table 2: Recommended Existing Regression Tests**:
   - Test File Path (e.g., `tests/test_calculator.py`).
   - Test Function / Suite Name.
   - Target Component.
   - Historical Relevance Score (percentage match based on path distance and co-change frequency).
4. **Card 3: Synthesized Candidate Tests (if enabled)**:
   - Test function name with AST syntax validation badge (`AST Syntax Valid`).
   - AI generation rationale explaining coverage gaps.
   - Monospace syntax-highlighted code block ready to copy into the test suite.
5. **Timeline 4: Grounded Historical Evidence**:
   - Collapsible list of historical commits, GitHub issues, and PR discussions retrieved from repository memory.
   - Commit SHA badge, source type pill (`COMMIT`, `ISSUE`, `PR`), semantic similarity percentage, and original commit message.
6. **Smooth Auto-Scroll (`useRef`)**:
   - Uses a React `useRef` attached to the results container:
     ```ts
     useEffect(() => {
       if (result && resultsRef.current) {
         resultsRef.current.scrollIntoView({ behavior: 'smooth', block: 'start' });
       }
     }, [result]);
     ```
   - Automatically scrolls the user smoothly down to the analysis report the moment results arrive.

---

### 5.4 Repository Code Explorer (`ExplorerView.tsx`)

#### Purpose
A dual-pane IDE-style code viewer enabling developers to browse files in the active repository, inspect directory structures, and view source code with line numbers.

#### Architecture
- **Left Pane (File Tree & Search)**:
  - Fetches the repository file index via `fetchRepositoryFiles(activeRepo.repository_id)` (`GET /repository-files`).
  - Search input filtering files in real time by path or filename.
  - File list displaying file name, relative directory path, and file size in KB.
  - Clickable rows that load the selected file into the right-hand code viewer.
- **Right Pane (Code Syntax Viewer)**:
  - Fetches UTF-8 content via `fetchRepositoryFileContent(activeRepo.repository_id, path)` (`GET /repository-file-content`).
  - Security-hardened backend prevents directory traversal attacks outside the repository root.
  - Displays file metadata (path, line count, file size).
  - One-click **Copy Source Code** action with visual checkmark feedback.
  - Formatted monospace code view with line numbers and horizontal scrolling.

---

### 5.5 CI/CD Integration (`CicdView.tsx`)

#### Purpose
Enables 1-click installation of the automated History-RAG CI/CD workflow into any GitHub repository via Pull Request or direct commit.

#### Workflow & Controls
1. **4-Step Onboarding Guide**: Explains how History-RAG intercepts Pull Requests, runs change-impact analysis, executes recommended tests, and posts automated governance review comments.
2. **Git Credentials Auto-Detection Banner**: Checks the local Git Credential Manager and displays the authenticated username (`AkanshaSrivastava17`).
3. **Configuration Form**:
   - GitHub Repository URL or Slug (`https://github.com/owner/repo`).
   - Setup Branch Name (defaults to `historyrag-ai-cicd-setup`).
   - Optional Personal Access Token input with visibility toggle.
   - Installation Mode:
     - *Create Onboarding Pull Request* (recommended).
     - *Direct Commit to Default Branch*.
   - **Simulation / Dry-Run Mode Toggle**: Allows testing the workflow generator and previewing the generated PR without writing to the remote repository.
4. **Action Button**: `1-Click Install CI/CD into Repository` calls `installWorkflow(...)` (`POST /devops/install-workflow`).
5. **Workflow YAML Preview**: Displays the exact generated `.github/workflows/historyrag.yml` GitHub Actions pipeline with copy action.
6. **Live Outcome Card**: On success, displays the generated PR URL (e.g., `https://github.com/owner/repo/pull/101`), target branch, and commit SHA.

---

### 5.6 Policy Gate & Rollback Manager (`PolicyGateView.tsx`)

#### Purpose
Simulates enterprise merge gates and controls automated container rollbacks when candidate deployments fail staging health checks.

#### Dual-Pane Architecture
- **Left Pane (Policy Gate Controls & Staging Health)**:
  - **Impact Level Selector**: `LOW`, `MEDIUM`, `HIGH`.
  - **AI Confidence Slider**: Range input from 50% to 100%.
  - **Test Execution Counts**: Inputs for `Tests Passed` and `Tests Failed`.
  - **Strict Mode Toggle**: Automatically block on HIGH impact changes.
  - **Evaluate Policy Gate Button**: Submits payload to `evaluateGate(...)` (`POST /evaluate-gate`).
  - **Deployment Health Card**: Displays `CURRENT IMAGE` (`historyrag:v1.0.0-stable`) and `KNOWN GOOD POINTER`.
  - **Emergency Rollback Action**: Confirmation-gated modal triggering `triggerRollback(...)` (`POST /devops/rollback`).
- **Right Pane (Gate Evaluation Outcome & Bot Review Preview)**:
  - **Decision Banner**: Large color-coded outcome banner:
    - `APPROVED (Merge Safe)` in Emerald Green.
    - `WARNING (Review Required)` in Amber Yellow.
    - `BLOCKED` in Rose Red.
  - **Policy Violations List**: Specific rules violated (e.g., *"Blocked: Critical component(s) ['core'] affected with 2 failing regression test(s)"*).
  - **Recommendations & Warnings List**: Actionable guidance (e.g., low confidence or missing tests).
  - **Live Bot Review Preview**: Formatted terminal preview demonstrating how `github-actions[bot]` posts the evaluation table directly on GitHub Pull Requests.

---

### 5.7 Observability & Telemetry (`ObservabilityView.tsx`)

#### Purpose
Provides real-time production telemetry by directly consuming and parsing Prometheus OpenMetrics from the backend `/metrics` endpoint.

#### OpenMetrics Parser (`parsePrometheusMetrics`)
The frontend includes a custom, regex-based Prometheus parser that extracts:
- Total Invocations (`historyrag_change_analysis_total`).
- Cache Hits (`historyrag_retrieval_cache_hits_total`).
- Policy Gate Rejections (`historyrag_pipeline_gate_decisions_total{decision="BLOCKED"}`).
- Latency Quantiles (`historyrag_analysis_latency_seconds{quantile="0.5"}`, `0.9`, `0.95`).
- Mode Distribution (counters grouped by evaluation mode).

#### UI Visualizations
1. **4 Top KPI Cards**: Total Invocations, Cache Hit Ratio, Policy Gate Rejections, Average Latency.
2. **Quantile Latency Breakdown**: 3 cards displaying P50 (median), P90 (90th percentile), and P95 (tail latency) in milliseconds.
3. **Evaluation Mode Distribution**: Horizontal proportional bars showing usage across `History-RAG`, `Semantic-only`, `History-RAG + Graph`, and `LLM-only`.
4. **Raw OpenMetrics Stream Viewer**: Monospace code viewer showing the raw Prometheus payload with a one-click copy button and refresh action.

---

## 6. API Integration Layer & Data Contracts

All communication between the React frontend and FastAPI backend is centralized in `frontend/src/services/api.ts` with strict TypeScript data types in `frontend/src/types/api.ts`.

### 6.1 Stream-Safe HTTP Client (`request<T>`)
A major architectural feature is the stream-safe error handler. When an HTTP error occurs (e.g., `400 Bad Request` or `502 Bad Gateway`), reading `res.json()` can fail if the body is HTML or plain text. Calling `res.text()` afterwards throws `TypeError: body stream already read`.

To prevent this, the client reads the body **once** as text and parses it safely:
```ts
async function request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const url = `${API_BASE}${endpoint}`;
  try {
    const res = await fetch(url, {
      ...options,
      headers: { Accept: 'application/json', ...(options.headers || {}) },
    });

    if (!res.ok) {
      let errorMsg = `Server returned status ${res.status}`;
      try {
        const text = await res.text();
        try {
          const errorData = JSON.parse(text);
          if (errorData.detail) errorMsg = errorData.detail;
          else if (errorData.message) errorMsg = errorData.message;
        } catch {
          if (text) errorMsg = text.slice(0, 300);
        }
      } catch { /* fallback */ }
      throw new ApiError(errorMsg, res.status);
    }

    const contentType = res.headers.get('content-type') || '';
    if (contentType.includes('application/json')) {
      return (await res.json()) as T;
    }
    return (await res.text()) as unknown as T;
  } catch (err: unknown) {
    if (err instanceof ApiError) throw err;
    const message = err instanceof Error ? err.message : 'Network request failed';
    throw new ApiError(`Unable to connect to History-RAG backend: ${message}`);
  }
}
```

### 6.2 Endpoint Inventory

| Endpoint | Method | Service Function | Payload / Parameters | Return Type |
| :--- | :---: | :--- | :--- | :--- |
| `/health` | `GET` | `fetchHealth()` | None | `HealthResponse` |
| `/repositories` | `GET` | `fetchRepositories()` | None | `RepositoryItem[]` |
| `/repository-status` | `GET` | `fetchRepositoryStatus(id)` | `repository_id: string` | `RepositoryStatusResponse` |
| `/upload-repository` | `POST` | `uploadRepositoryZip(file, id)` | `FormData (file, repository_id)` | Upload status & stats |
| `/index` | `POST` | `cloneRepository(url, id)` | `{ repository_url, repository_id }` | Index status & docs |
| `/repository-files` | `GET` | `fetchRepositoryFiles(id)` | `repository_id: string` | `{ files: RepositoryFileItem[] }` |
| `/repository-file-content` | `GET` | `fetchRepositoryFileContent(id, path)` | `repository_id, file_path` | `{ content: string }` |
| `/analyze-change` | `POST` | `analyzeChange(payload)` | `AnalyzeChangeRequest` | `AnalyzeChangeResponse` |
| `/evaluate-gate` | `POST` | `evaluateGate(payload)` | `GateEvaluationRequest` | `GateEvaluationResponse` |
| `/devops/install-workflow` | `POST` | `installWorkflow(payload)` | `WorkflowInstallRequest` | `WorkflowInstallResponse` |
| `/devops/deployments` | `GET` | `fetchDeployments()` | None | `DeploymentLedgerResponse` |
| `/devops/rollback` | `POST` | `triggerRollback(payload)` | `{ failed_image, reason, environment }` | `RollbackResponse` |
| `/metrics` | `GET` | `fetchRawMetrics()` | None | `string` (Prometheus text) |

---

## 7. Defensive Engineering & Error Resiliency

To prevent client-side crashes, the frontend implements multi-layered defensive patterns:

1. **Null-Safe Property Accessors**:
   - Scores: `(c.score ?? 0).toFixed(2)` prevents `undefined.toFixed()` errors.
   - Relevance: `((t.relevance_score ?? t.score ?? 0) * 100).toFixed(0)%`.
   - Reason lists: Checks both `c.reasons` (array) and `c.reason` (string) with fallback defaults.
2. **Defensive Historical Evidence Source Types**:
   - Backend Git commit records sometimes omit `source_type`. The frontend dynamically infers the type from the ID prefix:
     ```tsx
     {(ev.source_type || (ev.id?.startsWith('commit') ? 'commit' : ev.id?.startsWith('issue') ? 'issue' : 'evidence')).toUpperCase()}
     ```
3. **Policy Gate Field Normalization**:
   - Supports both `violations` and `blocking_reasons`, as well as `recommendations` and `warnings`, accommodating both legacy and updated backend responses without crashing.
4. **Host Machine Socket Abort (`[WinError 10053]`) Handling**:
   - When Windows security blocks outbound HTTPS connections to `api.github.com`, the backend installer catches the socket exception and falls back to **Dry-Run Simulation**, generating the complete workflow YAML and sample PR preview rather than halting.

---

## 8. Build Pipeline & Production Deployment

### 8.1 Vite & Tailwind CSS v4 Configuration
- **Vite 6** (`frontend/vite.config.ts`):
  - Integrates `@vitejs/plugin-react` and `@tailwindcss/vite`.
  - Configures a dev server proxy forwarding `/api/*` to `http://localhost:8000/*` with path rewriting:
    ```ts
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, ''),
      },
    }
    ```
- **Tailwind CSS v4** (`frontend/src/index.css`):
  - Employs `@import "tailwindcss";` eliminating legacy `tailwind.config.js` bloat.
  - Custom design tokens for table headers, borders, and monospace fonts.

### 8.2 Production Compilation
Executing `npm run build` runs `tsc -b && vite build`. Production output:
```
dist/index.html                   0.96 kB │ gzip:  0.54 kB
dist/assets/index-DH1wy9yM.css   33.63 kB │ gzip:  7.04 kB
dist/assets/index-DhD50Myr.js   312.65 kB │ gzip: 89.77 kB
✓ built in 1.12s
```

### 8.3 FastAPI Static Mount
In production, the compiled static bundle (`frontend/dist`) is directly served by FastAPI at `/dashboard/` in `app/api/routes.py`:
```python
_frontend_dist = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "frontend", "dist")
if os.path.exists(_frontend_dist):
    app.mount("/dashboard", StaticFiles(directory=_frontend_dist, html=True), name="dashboard")

    @app.get("/app", include_in_schema=False)
    def redirect_to_dashboard():
        return RedirectResponse(url="/dashboard/")
```
Accessing `http://localhost:8000/app` automatically redirects to the embedded React dashboard.

---

## 9. Developer Operations & Execution Guide

### 9.1 Starting the Complete Environment

#### 1. FastAPI Backend (Port 8000)
```powershell
uvicorn app.api.routes:app --host 0.0.0.0 --port 8000
```
- Interactive Swagger API Documentation: `http://localhost:8000/docs`
- Embedded Production Dashboard: `http://localhost:8000/dashboard/`

#### 2. React Frontend Dev Server (Port 3000)
```powershell
cd frontend
npm run dev -- --host 0.0.0.0 --port 3000
```
- Modern SaaS Application: `http://localhost:3000`

#### 3. Classic Streamlit Interface (Port 8501)
```powershell
streamlit run ui/app.py --server.port 8501
```
- Streamlit Workbench: `http://localhost:8501`

### 9.2 Quality Assurance & Testing
- **TypeScript & Linting**:
  ```powershell
  cd frontend
  npm run build
  npx oxlint
  ```
- **Full Backend Pytest Suite**:
  ```powershell
  pytest -v
  ```
  *(All 61 test cases across 13 test suites pass with 100% success).*

---
*Author: DeepMind Antigravity Engineering*  
*Repository: [AkanshaSrivastava17/AIDevops](https://github.com/AkanshaSrivastava17/AIDevops)*
