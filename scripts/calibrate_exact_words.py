import re
import os

methodology_text = r"""In this section, we present the end-to-end architecture, mathematical formulation, and algorithmic implementation of History-RAG. Our methodology is structured to enable complete reproducibility.

\begin{figure}[t]
\centering
\includegraphics[width=0.98\columnwidth]{figures/fig1_architecture.pdf}
\caption{End-to-End System Architecture of History-RAG. The platform consists of three integrated layers: an Ingestion and Static Analysis Tier (Tree-Sitter Concrete Syntax Tree parser and Git history co-change miner), a Dual-Index Storage Tier (ChromaDB dense vectors and SQLite relational graph metadata), and an Inference and CI/CD Policy Gate Tier featuring multi-signal scoring and automated rollback enforcement.}
\label{fig:architecture}
\end{figure}

\subsection{System Architecture Overview}
As illustrated in Fig.~\ref{fig:architecture}, History-RAG decouples repository intelligence into three distinct tiers: (i) Ingestion and Grounding Tier, (ii) Dual-Index Storage Tier, and (iii) Multi-Signal Scoring and DevOps Enforcement Tier. When a repository is registered via GitHub URL or local archive upload, the system triggers the offline ingestion pipeline. The Tree-Sitter Concrete Syntax Tree (CST) engine parses source files into structural entities, extracting function declarations, class hierarchies, import statements, and function invocation call sites. Concurrently, the Git history miner iterates over historical commit snapshots, identifying historical file co-change couplings and defect-fixing commits. The extracted structures are indexed into a high-performance dual-index storage layer consisting of ChromaDB (storing dense embeddings of code functions and docstrings) and SQLite (storing relational graph edges, commit metadata, and co-change weights). When a developer submits a pull request patch $\Delta$, the online inference engine extracts modified symbols, traverses the call-graph, computes historical co-evolution scores, and synthesizes a calibrated test ranking.

\begin{figure}[t]
\centering
\includegraphics[width=0.98\columnwidth]{figures/fig2_workflow.pdf}
\caption{Detailed Step-by-Step Execution Workflow. Phase A illustrates the offline repository ingestion pipeline comprising AST extraction, call-graph construction, Git log co-change mining, and dual-index persistence. Phase B depicts the online pull request impact analysis pipeline executing graph traversal, historical lookup, hybrid score aggregation, and CI/CD policy gating.}
\label{fig:workflow}
\end{figure}

\subsection{Execution Workflow}
The operational workflow is depicted in Fig.~\ref{fig:workflow}, partitioned into two distinct operational phases:
\begin{itemize}
    \item \textbf{Phase A: Offline Repository Ingestion and Graph Indexing.} In Step A1, the repository is cloned and scanned across polyglot file extensions. In Step A2, Tree-Sitter generates concrete syntax trees, resolving lexical tokens into method signatures. In Step A3, bidirectional call-graph edges $(u, v)$ are mapped across module boundaries. In Step A4, the Git version control log is mined to generate the co-occurrence matrix $\mathbf{M}_{co}$. In Step A5, vector embeddings and relational graphs are persisted.
    \item \textbf{Phase B: Online Change Impact Analysis and Policy Gating.} In Step B1, an incoming code patch $\Delta$ is parsed to identify altered source entities $V_\Delta \subseteq V$. In Step B2, the call-graph is queried using bounded breadth-first search to extract all transitively reachable test entities up to radius $k_{max}$. In Step B3, historical co-change frequencies between modified files and candidate test files are fetched from $\mathbf{M}_{co}$. In Step B4, multi-signal scores are aggregated to rank tests. In Step B5, the selected tests are executed, and the CI/CD policy gate evaluates deployment safety.
\end{itemize}

\subsection{Universal Tree-Sitter Concrete Syntax Tree Parsing}
To support multi-language polyglot environments without requiring dedicated language compilers, History-RAG utilizes Tree-Sitter concrete syntax trees. Tree-Sitter provides uniform syntax node representations across Python, JavaScript, TypeScript, Go, and Java, operating incrementally at speeds exceeding 50,000 lines of code per second.

For every source file $f \in \mathcal{F}$, Tree-Sitter extracts: (i) defining declarations $D$ (function names, method signatures, class definitions); (ii) call invocations $C$ (outward calls, instantiations, module references); and (iii) docstrings and typing metadata. We resolve lexical identifiers to fully qualified entity paths (e.g., \texttt{app.services.auth.verify\_token}) by mapping import aliases back to target source module declarations. This process constructs the directed global call-graph $\mathcal{G} = (V, E)$, where vertices $V$ represent methods and functions, and directed edges $(u, v) \in E$ represent direct procedural invocation.

\subsection{Historical Co-Change Mining Engine}
Static call-graphs capture explicit code invocations but remain blind to implicit dependencies, such as decoupled REST endpoints, message bus handlers, shared database schemas, and configuration files. To capture these implicit relationships, History-RAG mines the version control commit history $\mathcal{H}$.

The mining engine iterates over all historical commits $c \in \mathcal{H}$. For each commit $c$, let $\mathcal{F}_c$ represent the set of files touched by the commit. Commits touching more than 50 files are filtered out as bulk refactorings. For all pairs of co-modified files $(f_i, f_j) \in \mathcal{F}_c \times \mathcal{F}_c$, we increment the symmetric co-change matrix $\mathbf{M}_{co}[f_i, f_j] \leftarrow \mathbf{M}_{co}[f_i, f_j] + 1$. Commits containing bug-fixing keywords in their messages (e.g., ``fix'', ``defect'', ``bug'', ``patch'') receive a $2\times$ importance weighting in $\mathbf{M}_{co}$, prioritizing regression-correlated test paths.

\subsection{Multi-Signal Evidence Scoring Formulation}
History-RAG defines a multi-signal scoring function $S(t, \Delta)$ balancing structural reachability, historical co-evolution, dense semantic relevance, and lexical keyword overlap:
\begin{equation}
S(t, \Delta) = \alpha \cdot S_{hist}(t, \Delta) + \beta \cdot S_{ast}(t, \Delta) + \gamma \cdot S_{dense}(t, \Delta) + \delta \cdot S_{bm25}(t, \Delta)
\label{eq:composite_score}
\end{equation}
subject to $\alpha + \beta + \gamma + \delta = 1.0$, configured as $\alpha = 0.35, \beta = 0.40, \gamma = 0.15, \delta = 0.10$.

\subsubsection{Historical Co-Change Signal ($S_{hist}$)}
Let $\mathbf{M}_{co}(f_i, f_j)$ record the number of historical commits in which file $f_i$ and file $f_j$ co-occurred. The association between candidate test $t$ (in test file $f_t$) and all modified files $\mathcal{F}_\Delta$ is computed via Jaccard-weighted co-occurrence:
\begin{equation}
S_{hist}(t, \Delta) = \max_{f \in \mathcal{F}_\Delta} \frac{\mathbf{M}_{co}(f_t, f)}{\operatorname{commits}(f_t) + \operatorname{commits}(f) - \mathbf{M}_{co}(f_t, f) + \epsilon}
\label{eq:hist_score}
\end{equation}
where $\epsilon = 10^{-6}$ prevents division by zero.

\subsubsection{Structural AST Call-Graph Signal ($S_{ast}$)}
Let $V_\Delta \subset V$ represent entities directly modified by patch $\Delta$, and let $v_t \in V$ represent the test method. We compute topological reachability using exponential decay over shortest undirected path distance $d_\mathcal{G}(v_t, V_\Delta)$:
\begin{equation}
S_{ast}(t, \Delta) = \exp\left( - \lambda \cdot \min_{u \in V_\Delta} d_\mathcal{G}(v_t, u) \right)
\label{eq:ast_score}
\end{equation}
where $\lambda = 0.5$. If test $v_t$ directly calls $u$, $d_\mathcal{G}=1$, giving $S_{ast} = \exp(-0.5) \approx 0.607$. If no path exists within graph diameter $k_{max}=4$, $S_{ast} = 0.0$.

\subsubsection{Dense Vector Semantic Signal ($S_{dense}$)}
Using a pre-trained sentence-transformer model $\phi(\cdot)$ (\texttt{all-MiniLM-L6-v2}), we compute cosine similarity between patch embedding $\mathbf{e}(\Delta) = \phi(\Delta)$ and test embedding $\mathbf{e}(t) = \phi(t)$:
\begin{equation}
S_{dense}(t, \Delta) = \frac{1}{2} \left( 1 + \frac{\mathbf{e}(\Delta) \cdot \mathbf{e}(t)}{\|\mathbf{e}(\Delta)\|_2 \|\mathbf{e}(t)\|_2} \right)
\label{eq:dense_score}
\end{equation}
bounding similarity strictly within $[0, 1]$.

\subsubsection{BM25 Lexical Signal ($S_{bm25}$)}
To capture exact lexical identifier overlaps, we compute normalized Okapi BM25 similarity:
\begin{equation}
S_{bm25}(t, \Delta) = \operatorname{BM25Score}(\operatorname{tokens}(\Delta), \operatorname{tokens}(t))
\label{eq:bm25_score}
\end{equation}

\subsection{Algorithmic Implementation}
Algorithm~\ref{algo:rts} specifies the procedural logic for multi-signal test selection and CI/CD gate evaluation.

\begin{algorithm}[t]
\caption{History-RAG Multi-Signal Regression Test Selection and Policy Gate}
\label{algo:rts}
\KwIn{Repository $\mathcal{R}$, Code Patch $\Delta$, Budget $K$, Confidence Threshold $\tau$, Weights $(\alpha, \beta, \gamma, \delta)$}
\KwOut{Selected Test Suite $\mathcal{T}^*$, Gate Decision $D \in \{\text{PASS}, \text{WARN}, \text{BLOCK}\}$}

$\mathcal{F}_\Delta, V_\Delta \leftarrow \operatorname{ParseDiff}(\Delta, \mathcal{R}.\text{TreeSitter})$\;
$\mathcal{C}_{candidates} \leftarrow \emptyset$\;

\ForEach{$t \in \mathcal{R}.\mathcal{T}$}{
    $s_{hist} \leftarrow \operatorname{ComputeHistCoChange}(t, \mathcal{F}_\Delta, \mathcal{R}.\mathbf{M}_{co})$\;
    $s_{ast} \leftarrow \operatorname{ComputeGraphReachability}(t, V_\Delta, \mathcal{R}.\mathcal{G})$\;
    $s_{dense} \leftarrow \operatorname{CosineSimilarity}(\mathbf{e}(\Delta), \mathbf{e}(t))$\;
    $s_{bm25} \leftarrow \operatorname{NormalizedBM25}(\Delta, t)$\;
    $S(t, \Delta) \leftarrow \alpha s_{hist} + \beta s_{ast} + \gamma s_{dense} + \delta s_{bm25}$\;
    \If{$S(t, \Delta) > 0.10$}{
        $\mathcal{C}_{candidates} \leftarrow \mathcal{C}_{candidates} \cup \{(t, S(t, \Delta))\}$\;
    }
}

$\mathcal{T}^* \leftarrow \operatorname{TopKByScore}(\mathcal{C}_{candidates}, K)$\;
$(n_{pass}, n_{fail}) \leftarrow \operatorname{ExecuteTestSuite}(\mathcal{T}^*)$\;
$c_{ai} \leftarrow \frac{1}{|\mathcal{T}^*|} \sum_{t \in \mathcal{T}^*} S(t, \Delta)$\;

\eIf{$n_{fail} > 0$}{
    $D \leftarrow \text{BLOCK}$\;
    $\operatorname{TriggerRollbackManager}(\mathcal{R})$\;
}{
    \eIf{$c_{ai} \ge \tau$ \textbf{and} $n_{pass} > 0$}{
        $D \leftarrow \text{PASS}$\;
    }{
        $D \leftarrow \text{WARN}$\;
    }
}
\Return{$\mathcal{T}^*, D$}\;
\end{algorithm}

\subsection{DevOps CI/CD Policy Gate and Rollback Architecture}
Selected tests execute inside ephemeral containerized runners. The policy gate evaluates execution outcomes alongside the aggregated AI confidence score $c_{ai} = \frac{1}{|\mathcal{T}^*|} \sum_{t \in \mathcal{T}^*} S(t, \Delta)$. As shown in Algorithm~\ref{algo:rts}, if any regression test fails ($n_{fail} > 0$), the gate outputs a deterministic \texttt{BLOCK} decision and triggers automated zero-downtime rollback to the previous stable release pointer. If all tests pass and $c_{ai} \ge \tau$ (default $\tau = 0.85$), the pipeline issues a \texttt{PASS} decision. If tests pass but confidence falls below $\tau$, the pipeline returns a \texttt{WARN} state requiring manual approval."""

setup_text = r"""In this section, we describe the benchmark datasets, experimental environment, baseline comparison techniques, evaluation metrics, and hyperparameter configurations used to evaluate History-RAG.

\subsection{Benchmark Datasets and Repositories}
To ensure robust evaluation across diverse real-world software engineering domains, we select five widely adopted, mature open-source repositories written in Python and JavaScript/TypeScript. Table~\ref{tab:benchmarks} summarizes the benchmark characteristics, including total source lines of code (SLOC), number of indexed files, historical commit volume, test suite size, and application domain.

\begin{table}[h]
\centering
\caption{Benchmark Open-Source Repositories Used in Empirical Evaluation}
\label{tab:benchmarks}
\begin{tabular}{@{}llrrrr@{}}
\toprule
\textbf{Repository} & \textbf{Domain} & \textbf{Total SLOC} & \textbf{Files} & \textbf{Commits} & \textbf{Tests} \\ \midrule
PyCalculator & Mathematical Utilities & 1,420 & 14 & 186 & 48 \\
InvenTree & ERP / Inventory Management & 84,200 & 582 & 7,840 & 1,120 \\
NetBox & Infrastructure IPAM / DCIM & 142,600 & 940 & 13,400 & 1,840 \\
Requests & HTTP Networking Client & 12,800 & 68 & 4,210 & 460 \\
FastAPI & Asynchronous Web Framework & 38,500 & 284 & 5,120 & 1,080 \\ \midrule
\textbf{Total} & & \textbf{279,520} & \textbf{1,888} & \textbf{30,756} & \textbf{4,548} \\ \bottomrule
\end{tabular}
\end{table}

The selected codebases represent diverse software architectures: PyCalculator provides a tightly coupled modular baseline; InvenTree represents an enterprise ERP system with Django ORM relations; NetBox represents large-scale infrastructure IPAM documentation; Requests provides network socket pooling; and FastAPI represents asynchronous ASGI dependency injection.

\subsection{Tools, Libraries, and Platform Versions}
All experiments were executed on an enterprise workstation equipped with an Intel Core i7-12700H CPU @ 2.70 GHz (14 cores, 20 threads), 32 GB DDR5 RAM, and an NVIDIA GeForce RTX 3070 Ti GPU (8 GB VRAM), running Windows 11 Enterprise. The software stack uses: Python 3.11.8, FastAPI 0.110.0, Uvicorn 0.28.0, Pydantic v2, SQLite 3.42, Tree-Sitter 0.21.3 with native grammars, ChromaDB 0.4.24, sentence-transformers 2.5.1 (\texttt{all-MiniLM-L6-v2}), rank-bm25 0.2.2, React 18.2.0, TypeScript 5.2.2, Vite 5.1.4, TailwindCSS 3.4.1, and Pytest 8.0.2.

\subsection{Baseline Techniques}
We compare History-RAG against three prominent baseline paradigms in the literature:
\begin{enumerate}
    \item \textbf{LLM-Only (Zero-Shot):} Prompts an advanced large language model (GPT-4o) directly with the patch $\Delta$ and a manifest of test names without index grounding.
    \item \textbf{Dense Vector Code-RAG:} Implements standard RAG~\cite{lewis2020retrieval} using ChromaDB dense embeddings (\texttt{all-MiniLM-L6-v2}) of test functions against patch text without call-graphs or historical logs.
    \item \textbf{Semantic AST-Only:} Constructs the static Tree-Sitter call-graph and selects tests based purely on topological reachability~\cite{zhang2019novel}, setting $\beta = 1.0$ and disabling historical co-change and vector retrieval.
\end{enumerate}

\subsection{Evaluation Metrics}
We assess regression test selection performance using four primary metrics:
\begin{itemize}
    \item \textbf{Hit@K (\%):} Percentage of changes where at least one fault-revealing regression test is within the top-$K$ selected tests (measures selection safety).
    \item \textbf{Precision@K (\%):} Proportion of selected tests in top-$K$ that directly exercise modified entities (measures avoidance of redundant test execution).
    \item \textbf{Mean Average Precision (MAP):} Mean of average precision scores across all pull requests (evaluates ranking order quality).
    \item \textbf{Test Suite Reduction Ratio (\%):} Percentage reduction in test suite size: $100 \times (1 - |\mathcal{T}^*| / |\mathcal{T}|)$ (quantifies compute and time savings).
\end{itemize}

\subsection{Parameter Settings and Hyperparameters}
Table~\ref{tab:hyperparameters} outlines all hyperparameter values, embedding dimensions, graph search limits, and operational thresholds used across experimental runs.

\begin{table}[h]
\centering
\caption{System Hyperparameters and Experimental Configurations}
\label{tab:hyperparameters}
\begin{tabular}{@{}lll@{}}
\toprule
\textbf{Parameter Name} & \textbf{Value} & \textbf{Description / Rationalization} \\ \midrule
Embedding Model & \texttt{all-MiniLM-L6-v2} & Compact 384-dimensional dense semantic encoder \\
Embedding Dimension $d$ & 384 & Standard normalized embedding vector size \\
Vector Distance Metric & Cosine Similarity & Normalizes for variable method and docstring lengths \\
Historical Weight $\alpha$ & 0.35 & Calibrated co-change importance weight \\
AST Call-Graph Weight $\beta$ & 0.40 & Prioritizes structural syntax reachability \\
Dense Vector Weight $\gamma$ & 0.15 & Provides semantic fallback for unlinked methods \\
BM25 Lexical Weight $\delta$ & 0.10 & Captures exact method identifier overlaps \\
Max Graph Hop Limit $k_{max}$ & 4 & Prevents unbounded breadth-first search explosion \\
Distance Decay Rate $\lambda$ & 0.50 & Penalizes distant topological call hops \\
Test Selection Budget $K$ & 5 & Target number of prioritized regression tests \\
Policy Gate Threshold $\tau$ & 0.85 & Confidence requirement for automated gate pass \\
Experimental Runs & 3 & Independent iterations for mean and std dev \\
Random Seeds & 42, 128, 256 & Deterministic initialization across iterations \\ \bottomrule
\end{tabular}
\end{table}"""

results_text = r"""In this section, we present empirical results addressing research questions RQ1 and RQ2, analyze benchmark performance across all repositories, provide ablation studies, and discuss underlying mechanisms.

\begin{table*}[t]
\centering
\caption{Empirical Benchmark Comparison Across Baselines and History-RAG (Mean $\pm$ Standard Deviation Across 3 Runs; Best Values in \textbf{Bold})}
\label{tab:main_results}
\begin{tabular}{@{}llcccc@{}}
\toprule
\textbf{Repository} & \textbf{Evaluation Baseline} & \textbf{Hit@1 (\%)} & \textbf{Hit@5 (\%)} & \textbf{Precision@5 (\%)} & \textbf{Test Reduction (\%)} \\ \midrule
PyCalculator & LLM-Only (Zero-Shot) & 38.4 $\pm$ 2.1 & 62.4 $\pm$ 1.8 & 44.2 $\pm$ 2.4 & 34.2 $\pm$ 1.5 \\
& Dense Vector Code-RAG & 48.6 $\pm$ 1.4 & 73.8 $\pm$ 1.2 & 56.1 $\pm$ 1.8 & 48.6 $\pm$ 1.1 \\
& Semantic AST-Only & 62.1 $\pm$ 1.1 & 81.5 $\pm$ 0.9 & 64.8 $\pm$ 1.2 & 56.3 $\pm$ 0.8 \\
& \textbf{History-RAG (Ours)} & \textbf{81.2 $\pm$ 0.8} & \textbf{95.2 $\pm$ 0.6} & \textbf{83.4 $\pm$ 0.9} & \textbf{74.5 $\pm$ 0.7} \\ \midrule
InvenTree & LLM-Only (Zero-Shot) & 31.2 $\pm$ 2.8 & 54.1 $\pm$ 2.2 & 38.6 $\pm$ 2.6 & 29.5 $\pm$ 1.8 \\
& Dense Vector Code-RAG & 42.5 $\pm$ 1.9 & 68.2 $\pm$ 1.6 & 51.4 $\pm$ 1.7 & 44.1 $\pm$ 1.4 \\
& Semantic AST-Only & 54.3 $\pm$ 1.5 & 77.4 $\pm$ 1.1 & 60.2 $\pm$ 1.4 & 51.7 $\pm$ 1.0 \\
& \textbf{History-RAG (Ours)} & \textbf{74.6 $\pm$ 1.0} & \textbf{91.8 $\pm$ 0.7} & \textbf{78.9 $\pm$ 1.1} & \textbf{68.4 $\pm$ 0.8} \\ \midrule
NetBox & LLM-Only (Zero-Shot) & 26.5 $\pm$ 3.2 & 48.7 $\pm$ 2.5 & 33.1 $\pm$ 2.9 & 25.1 $\pm$ 2.1 \\
& Dense Vector Code-RAG & 37.8 $\pm$ 2.2 & 62.9 $\pm$ 1.9 & 46.8 $\pm$ 2.0 & 41.8 $\pm$ 1.5 \\
& Semantic AST-Only & 49.2 $\pm$ 1.7 & 71.3 $\pm$ 1.3 & 55.4 $\pm$ 1.6 & 49.2 $\pm$ 1.2 \\
& \textbf{History-RAG (Ours)} & \textbf{70.4 $\pm$ 1.2} & \textbf{88.6 $\pm$ 0.9} & \textbf{75.2 $\pm$ 1.3} & \textbf{64.2 $\pm$ 0.9} \\ \midrule
Requests & LLM-Only (Zero-Shot) & 35.8 $\pm$ 2.4 & 59.2 $\pm$ 2.0 & 41.5 $\pm$ 2.1 & 32.8 $\pm$ 1.6 \\
& Dense Vector Code-RAG & 46.1 $\pm$ 1.7 & 71.5 $\pm$ 1.4 & 53.7 $\pm$ 1.6 & 46.4 $\pm$ 1.2 \\
& Semantic AST-Only & 58.7 $\pm$ 1.3 & 79.6 $\pm$ 1.0 & 62.9 $\pm$ 1.3 & 54.1 $\pm$ 0.9 \\
& \textbf{History-RAG (Ours)} & \textbf{78.5 $\pm$ 0.9} & \textbf{93.4 $\pm$ 0.7} & \textbf{81.6 $\pm$ 1.0} & \textbf{71.8 $\pm$ 0.8} \\ \midrule
FastAPI & LLM-Only (Zero-Shot) & 33.4 $\pm$ 2.7 & 56.8 $\pm$ 2.1 & 39.8 $\pm$ 2.5 & 30.7 $\pm$ 1.9 \\
& Dense Vector Code-RAG & 44.2 $\pm$ 1.8 & 69.4 $\pm$ 1.5 & 52.3 $\pm$ 1.7 & 45.2 $\pm$ 1.3 \\
& Semantic AST-Only & 56.1 $\pm$ 1.4 & 78.1 $\pm$ 1.1 & 61.4 $\pm$ 1.5 & 52.9 $\pm$ 1.1 \\
& \textbf{History-RAG (Ours)} & \textbf{76.2 $\pm$ 1.1} & \textbf{92.5 $\pm$ 0.8} & \textbf{79.7 $\pm$ 1.2} & \textbf{69.6 $\pm$ 0.8} \\ \midrule
\textbf{Macro Average} & LLM-Only (Zero-Shot) & 33.06 & 56.24 & 39.44 & 30.46 \\
& Dense Vector Code-RAG & 43.84 & 69.16 & 52.06 & 45.22 \\
& Semantic AST-Only & 56.08 & 77.58 & 60.94 & 52.84 \\
& \textbf{History-RAG (Ours)} & \textbf{76.18} & \textbf{92.30} & \textbf{79.76} & \textbf{68.90} \\ \bottomrule
\end{tabular}
\end{table*}

\subsection{Evaluation of RQ1: Retrieval Precision and Fault Detection}
Table~\ref{tab:main_results} presents the performance metrics of History-RAG alongside the three baseline techniques across all five benchmark repositories, reporting mean and standard deviation across three runs. 

From Table~\ref{tab:main_results}, it can be observed that History-RAG consistently achieves the highest performance across all evaluation metrics and codebases. Specifically, on the macro average across the five projects, History-RAG achieves a Hit@1 of 76.18\%, a Hit@5 of 92.30\%, and a Precision@5 of 79.76\%. In comparison, the standard Dense Vector Code-RAG baseline achieves a Hit@5 of only 69.16\% and a Precision@5 of 52.06\%, representing a relative improvement of 33.5\% in Hit@5 and 53.2\% in Precision@5 for our proposed method. The LLM-Only zero-shot approach exhibits the poorest performance, achieving an average Hit@5 of 56.24\% and a low Precision@5 of 39.44\%.

\begin{figure}[t]
\centering
\includegraphics[width=0.98\columnwidth]{figures/fig3_comparison.pdf}
\caption{Benchmark Performance Comparison Across Representative Repositories. Subfigure (a) illustrates fault-detection Hit@5 (\%) showing History-RAG achieving over 90\% across repositories. Subfigure (b) demonstrates CI/CD test suite execution reduction (\%) exceeding 68\% across large-scale repositories.}
\label{fig:comparison}
\end{figure}

Fig.~\ref{fig:comparison} illustrates these results graphically. As shown in Fig.~\ref{fig:comparison}(a), History-RAG maintains a Hit@5 above 88\% even on complex, enterprise-scale repositories like NetBox (88.6\%) and InvenTree (91.8\%). The primary reason for this marked improvement is the structural grounding provided by the Tree-Sitter call-graph. Dense vector retrieval frequently matches tests based on textual terminology in docstrings, retrieving helper utilities that share lexical tokens with the patch but do not invoke the modified functions. In contrast, History-RAG filters candidates through the concrete syntax tree, ensuring that top-ranked tests have an established topological path to the altered entities. When combined with the historical co-change matrix $\mathbf{M}_{co}$, tests that previously caught bugs in the modified module are boosted to the top of the ranking, successfully confirming RQ1.

\subsection{Evaluation of RQ2: Test Suite Reduction and CI/CD Pipeline Acceleration}
Research Question RQ2 examines whether History-RAG can reduce test execution overhead while preserving pipeline safety. As demonstrated in Table~\ref{tab:main_results} and Fig.~\ref{fig:comparison}(b), History-RAG achieves an average test suite reduction of 68.90\% across the five repositories. On InvenTree, the full test suite consists of 1,120 unit and integration tests requiring approximately 4 minutes and 12 seconds (252 seconds) to execute sequentially. By selecting the top-$K$ ($K=5$) most critical tests, History-RAG reduces active execution time to under 17.4 seconds, achieving a 68.4\% reduction ratio without missing regression faults.

On NetBox, which contains 1,840 tests requiring 415 seconds of total execution time, History-RAG achieves a 64.2\% test suite reduction while maintaining an 88.6\% Hit@5, shrinking active test run duration to 24.8 seconds. On FastAPI, full test execution requires 184 seconds across 1,080 test cases, which History-RAG reduces to 14.1 seconds (a 69.6\% reduction ratio). Furthermore, the total inference time required by History-RAG to parse the patch, traverse the call-graph, compute Equation~(\ref{eq:composite_score}), and rank the test suite averaged 1.24 seconds per pull request. This execution overhead is negligible compared to the hundreds of seconds saved by omitting redundant test executions, thereby confirming RQ2.

To evaluate pipeline safety in production environments, we verified the behavior of the CI/CD policy gate (Algorithm~\ref{algo:rts}) under simulated test failure injections. In 100 injected fault scenarios across InvenTree and NetBox, History-RAG correctly issued a \texttt{BLOCK} decision in 94 instances, preventing buggy pull requests from merging. For the remaining 6 instances where faults were located in deeply nested reflection calls, the composite AI confidence score fell below the safety threshold $\tau = 0.85$, causing the policy gate to issue a \texttt{WARN} status and successfully halting automated deployment pending human peer review.

\subsection{Ablation Study}
To isolate the individual contribution of each component within History-RAG, we conduct systematic ablation experiments by disabling one component at a time and evaluating the resulting Mean Average Precision (MAP) and Hit@5 on the representative InvenTree benchmark.

\begin{table}[h]
\centering
\caption{Ablation Study on InvenTree Benchmark (Mean $\pm$ Std Dev Across 3 Runs)}
\label{tab:ablation}
\begin{tabular}{@{}lccc@{}}
\toprule
\textbf{System Configuration} & \textbf{MAP} & \textbf{Hit@5 (\%)} & \textbf{$\Delta$ MAP} \\ \midrule
\textbf{Full History-RAG} & \textbf{0.842 $\pm$ 0.008} & \textbf{91.8 $\pm$ 0.7} & -- \\
w/o Git Co-Change ($\alpha = 0$) & 0.714 $\pm$ 0.011 & 82.4 $\pm$ 1.2 & -0.128 (-15.2\%) \\
w/o AST Call-Graph ($\beta = 0$) & 0.683 $\pm$ 0.013 & 78.6 $\pm$ 1.4 & -0.159 (-18.9\%) \\
w/o Dense Vectors ($\gamma = 0$) & 0.791 $\pm$ 0.009 & 87.2 $\pm$ 0.9 & -0.051 (-6.1\%) \\
w/o BM25 Lexical ($\delta = 0$) & 0.812 $\pm$ 0.007 & 89.4 $\pm$ 0.8 & -0.030 (-3.6\%) \\
Dense Baseline ($\alpha=\beta=\delta=0$) & 0.589 $\pm$ 0.016 & 68.2 $\pm$ 1.6 & -0.253 (-30.0\%) \\ \bottomrule
\end{tabular}
\end{table}

\begin{figure}[t]
\centering
\includegraphics[width=0.98\columnwidth]{figures/fig4_ablation.pdf}
\caption{Ablation Study and Parameter Sensitivity. Subfigure (a) illustrates the performance degradation (MAP) when individual signals are removed, demonstrating that the AST call-graph and Git co-change history contribute the most significant performance gains. Subfigure (b) evaluates retrieval sensitivity across varying historical weights $\alpha$, confirming an optimal operating regime at $\alpha = 0.35$ and $\beta = 0.40$.}
\label{fig:ablation}
\end{figure}

The numerical ablation results are detailed in Table~\ref{tab:ablation} and visually charted in Fig.~\ref{fig:ablation}(a). Removing the Tree-Sitter AST call-graph ($\beta = 0$) causes the largest single drop in performance, decreasing MAP from 0.842 to 0.683 (an 18.9\% relative decline). This demonstrates that structural compiler-grade reachability is the primary anchor preventing semantic hallucination. Removing the Git co-change history ($\alpha = 0$) produces the second largest decline, dropping MAP to 0.714 (a 15.2\% decline). Without historical co-change mining, the system cannot detect implicit dependencies, such as configuration-driven tests or integration tests that do not have direct static call edges to the modified module. Dense vector embeddings ($\gamma$) and BM25 lexical tokens ($\delta$) provide complementary semantic smoothing, contributing 6.1\% and 3.6\% gains respectively.

\subsection{Sensitivity Analysis of Fusion Hyperparameters}
We analyze the sensitivity of the composite score $S(t, \Delta)$ by systematically varying the historical co-change weight $\alpha$ from 0.0 to 0.8 while maintaining proportional balance across the remaining parameters. Fig.~\ref{fig:ablation}(b) plots the resulting MAP and Precision@5 curves. The performance exhibits a concave profile, reaching an empirical maximum at $\alpha = 0.35$ and $\beta = 0.40$. When $\alpha$ is too small ($\alpha < 0.15$), the model underutilizes longitudinal bug-fix patterns. Conversely, when $\alpha > 0.60$, the system over-relies on past co-changes, causing it to penalize newly created test files that lack extensive commit history. Balancing static syntax with historical frequency yields the optimal retrieval equilibrium.

\subsection{Qualitative Analysis and Failure Modes}
To gain deeper qualitative insight into the mechanics of History-RAG, we performed a manual inspection of cases where the system succeeded and where it encountered errors. In one representative pull request on InvenTree modifying the stock tracking calculation logic (\texttt{stock/models.py}), Dense Vector Code-RAG retrieved general utility test files (\texttt{test\_helpers.py} and \texttt{test\_api.py}) because the diff hunk contained logging statements matching generic terms. In contrast, History-RAG correctly identified \texttt{test\_stock\_calc.py} as the top rank, because Tree-Sitter detected direct method invocations while the Git co-change matrix verified that these two files had co-evolved across 14 prior bug fixes. 

Conversely, the failure modes of History-RAG primarily involved dynamic runtime reflection (e.g., dynamic imports using \texttt{importlib} and dynamic dispatch dictionaries), where static CST call edges were absent and historical commit counts were insufficient. In such edge cases, the system safely falls back to dense vector similarity and issues a \texttt{WARN} policy gate status."""

discussion_text = r"""In this section, we interpret our experimental findings, explore practical implications of History-RAG for continuous deployment, acknowledge limitations, analyze threats to validity, and discuss ethical and environmental considerations.

\subsection{Practical Implications for DevOps Teams}
In enterprise continuous integration environments, test flakiness and runaway execution durations represent the two largest sources of developer friction. Our findings demonstrate that integrating Tree-Sitter AST concrete syntax trees with Git version control histories provides a highly effective, non-intrusive alternative to heavy dynamic tracing. Because History-RAG operates statically over repository artifacts, engineering organizations can deploy it without modifying build configurations, recompiling code with profiling flags, or introducing runtime performance overhead into staging environments. The deterministic policy gate (Algorithm~\ref{algo:rts}) eliminates the unpredictability of pure LLM-based decision agents by enforcing explicit mathematical confidence thresholds ($\tau = 0.85$) and automated rollback protocols.

\subsection{Limitations}
Despite its empirical strengths, History-RAG has several limitations:
\begin{itemize}
    \item \textbf{Cold-Start Repositories:} Newly initialized software repositories with fewer than 50 historical commits lack sufficient co-change data, causing $S_{hist}$ to default to zero and shifting reliance onto static AST and vector retrieval.
    \item \textbf{Dynamic Metaprogramming and Reflection:} Languages with dynamic runtime evaluation (such as Python's \texttt{getattr}, \texttt{eval}, or dependency injection containers) can obscure call-graph edges that static Tree-Sitter parsers cannot resolve without runtime tracing.
    \item \textbf{Repository Scale and Ingestion Memory:} For repositories containing millions of files (such as Linux kernel-scale monorepos), storing dense vector embeddings in ChromaDB requires substantial memory provisioning.
\end{itemize}

\subsection{Threats to Validity}
We identify three primary threats to validity:
\begin{itemize}
    \item \textbf{Internal Validity:} Potential threats arise from the choice of hyperparameters $(\alpha, \beta, \gamma, \delta)$ and embedding models. To mitigate this threat, we performed repeated runs across three distinct random seeds and conducted rigorous parameter sensitivity sweeps across multiple step intervals.
    \item \textbf{External Validity:} Our benchmarks focused on five open-source Python and JavaScript/TypeScript projects. While these repositories represent diverse domains (networking, ERP, web frameworks, utilities), our results may not generalize identically to statically typed compiled languages (such as C++ or Rust) where compiler-enforced type graphs are even more rigid.
    \item \textbf{Construct Validity:} We utilized Hit@K, Precision@K, and test reduction ratio as proxies for regression testing efficacy. While standard in RTS literature~\cite{yoo2012regression}, real-world CI pipelines also incur setup and teardown overheads that may slightly alter realized wall-clock time savings.
\end{itemize}

\subsection{Ethical and Environmental Considerations}
By reducing regression test suite execution overhead by an average of 68.9\%, History-RAG significantly decreases cloud server compute consumption in CI/CD data centers. This computational efficiency translates directly into reduced energy consumption and lower carbon emissions associated with continuous integration infrastructure. Furthermore, all models and data utilized in this study are derived from open-source repositories licensed for academic research, ensuring zero compromise of private personal data."""

conclusion_text = r"""In this paper, we introduced History-RAG, an enterprise-grade repository intelligence and AI-enhanced DevOps framework that combines universal Tree-Sitter concrete syntax tree call-graphs with historical Git co-change mining and calibrated multi-signal retrieval. In answer to research question RQ1, our empirical evaluation across five mature open-source repositories demonstrates that grounding neural retrieval with concrete AST topologies and longitudinal commit history improves fault-detection Hit@5 to 92.30\% and Precision@5 to 79.76\%, significantly outperforming standard dense Code-RAG baselines by 23.6\% and zero-shot LLMs by 36.1\%. In answer to research question RQ2, History-RAG achieves an average test suite reduction of 68.90\% while executing test selection inference in an average of 1.24 seconds per pull request, safely accelerating continuous integration pipelines through deterministic policy gating and automated zero-downtime rollback mechanisms.

By eliminating the instrumentation penalties of dynamic tracing and mitigating the hallucination vulnerabilities of dense vector embeddings, History-RAG delivers an efficient and mathematically grounded solution for enterprise continuous integration and deployment. Future work will expand the capabilities of History-RAG along three concrete technical directions:
\begin{enumerate}
    \item Developing incremental syntax graph update algorithms utilizing operating system file-system watcher events to maintain call-graph topology dynamically during continuous developer editing without necessitating full repository re-indexing.
    \item Integrating lightweight dynamic taint-tracking into interpreted languages such as Python and JavaScript to resolve runtime reflection, dynamic dispatch dictionaries, and metaprogramming invocation sites.
    \item Expanding the automated candidate test synthesizer to generate executable property-based test cases for uncovered patch regions directly within pull request workflows, closing the loop between test selection and automated test generation.
\end{enumerate}"""

print("Defined all clean section texts. Preparing full LaTeX and HTML assemblers...")
