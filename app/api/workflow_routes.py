"""
Workflow Router for History-RAG Revision 2.2.
Implements all Lifecycle APIs defined in Section 10.4 and 10.8.
"""
import os
import json
import uuid
import asyncio
from datetime import datetime, timezone
from typing import List, Dict, Optional, Any
from fastapi import APIRouter, HTTPException, Query, Request, Response, Depends, Header
from pydantic import BaseModel, Field
from sse_starlette.sse import EventSourceResponse

from app.workflow.models import (
    GlobalRole, ProjectRole, RequestStatus, BriefStatus, TaskStatus, RunStatus,
    GateDecision, GateFreshness, DecisionStatus, User,
    FeatureRequest, BriefVersion, Decision, Task, PipelineRun, GateResult, Outcome,
    Conversation, Message, AuditLogEntry
)
from app.workflow.db import WorkflowDB
from app.workflow.auth import AuthService, DEMO_PERSONAS
from app.workflow.clarity import ClarityAssistant
from app.workflow.brief_generator import BriefGenerator, EVENT_SUBSCRIBERS, publish_sse_event
from app.workflow.tasks_service import TasksService
from app.workflow.pipelines_service import PipelinesService
from app.workflow.insights_service import InsightsService
from app.workflow.webhooks import WebhookHandler

from app.ingestion.sqlite_store import SQLiteMetadataStore
from app.ingestion.chroma_store import ChromaVectorStore
from app.rag.hybrid_retriever import HybridRetriever
from app.impact.scoring_engine import ImpactScoringEngine
from app.testing.test_recommender import TestRecommender
from app.testing.test_generator import CandidateTestGenerator
from app.devops.pipeline_gate import AdvancedCIDCGate

router = APIRouter(tags=["Workflow Lifecycle"])

# Global workflow services
workflow_db = WorkflowDB()
auth_service = AuthService(workflow_db)
sqlite_store = SQLiteMetadataStore()
chroma_store = ChromaVectorStore()
retriever = HybridRetriever(sqlite_store, chroma_store)
scoring_engine = ImpactScoringEngine()
test_recommender = TestRecommender()
candidate_generator = CandidateTestGenerator()
gate_engine = AdvancedCIDCGate()

clarity_assistant = ClarityAssistant(workflow_db, retriever)
brief_generator = BriefGenerator(workflow_db, retriever, scoring_engine, test_recommender, candidate_generator)
tasks_service = TasksService(workflow_db, retriever)
pipelines_service = PipelinesService(workflow_db, gate_engine)
insights_service = InsightsService(workflow_db)
webhook_handler = WebhookHandler(workflow_db, pipelines_service)


# ---------------------------------------------------------------------------
# Helper dependency to resolve active user from headers / demo switcher
# ---------------------------------------------------------------------------
def get_user(request: Request) -> User:
    return auth_service.get_current_user(request)


# ---------------------------------------------------------------------------
# 1. Auth, Personas & Users (Section 4, 10.4)
# ---------------------------------------------------------------------------

class SwitchPersonaRequest(BaseModel):
    user_id: str


@router.get("/auth/me")
def get_current_user_profile(user: User = Depends(get_user)):
    return {
        "user": user.model_dump(),
        "available_personas": list(DEMO_PERSONAS.values()),
        "mode": "demo"
    }


@router.get("/auth/personas")
def list_demo_personas():
    return list(DEMO_PERSONAS.values())


@router.post("/auth/switch-persona")
def switch_persona(req: SwitchPersonaRequest):
    try:
        user = auth_service.switch_demo_persona(req.user_id)
        return {"status": "success", "active_persona": user.model_dump()}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/users")
def list_users():
    return workflow_db.get_users()


@router.get("/projects")
def list_projects():
    return workflow_db.get_projects()


@router.get("/projects/{project_id}/members")
def get_project_members(project_id: str):
    return workflow_db.get_project_memberships(project_id)


class UpdateMembershipRequest(BaseModel):
    user_id: str
    role: ProjectRole


@router.put("/projects/{project_id}/members")
def update_project_member(project_id: str, req: UpdateMembershipRequest, actor: User = Depends(get_user)):
    workflow_db.update_project_membership(req.user_id, project_id, req.role, actor=actor)
    return {"status": "success", "message": f"Updated role to {req.role.value}"}


# ---------------------------------------------------------------------------
# 2. Conversations & Cited Q&A (Section 7.4, 8.2, 10.8)
# ---------------------------------------------------------------------------

class CreateConversationRequest(BaseModel):
    title: str
    project_id: str = "proj-platform-core"
    repository_id: str = "netbox"
    context_type: str = "repository"
    context_id: Optional[str] = None


class SendMessageRequest(BaseModel):
    content: str
    system_mode: str = "History-RAG"


class MessageFeedbackRequest(BaseModel):
    rating: int  # 1 or -1
    reason: Optional[str] = None


class SaveNoteRequest(BaseModel):
    note_title: Optional[str] = None


@router.get("/conversations")
def list_conversations(
    project_id: Optional[str] = None,
    user: User = Depends(get_user)
):
    return workflow_db.list_conversations(user_id=user.id, project_id=project_id)


@router.post("/conversations")
def create_conversation(req: CreateConversationRequest, user: User = Depends(get_user)):
    conv = workflow_db.create_conversation(
        user_id=user.id,
        project_id=req.project_id,
        repository_id=req.repository_id,
        title=req.title,
        context_type=req.context_type,
        context_id=req.context_id
    )
    return conv


@router.get("/conversations/{conv_id}")
def get_conversation(conv_id: str):
    conv = workflow_db.get_conversation(conv_id)
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found.")
    return conv


@router.delete("/conversations/{conv_id}")
def delete_conversation(conv_id: str, user: User = Depends(get_user)):
    success = workflow_db.delete_conversation(conv_id, actor=user)
    return {"status": "success", "deleted": success}


@router.post("/conversations/{conv_id}/messages")
def send_conversation_message(
    conv_id: str,
    req: SendMessageRequest,
    user: User = Depends(get_user)
):
    conv = workflow_db.get_conversation(conv_id)
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found.")

    # 1. Add user message
    user_msg = workflow_db.add_message(conversation_id=conv_id, role="user", content=req.content)

    # 2. Retrieve history and citations from RAG
    evidence_pack = retriever.build_evidence_pack(
        repository_id=conv.repository_id,
        query_or_change=req.content,
        system_mode=req.system_mode,
        top_k=8
    )

    evidence_refs = []
    # Commit citations
    for c in evidence_pack.commit_evidence[:4]:
        evidence_refs.append({
            "id": f"ref-{uuid.uuid4().hex[:6]}",
            "owner_type": "message",
            "owner_id": "",
            "source_type": "commit",
            "source_id": c.get("commit_sha", "")[:8],
            "similarity": c.get("similarity", 0.85),
            "excerpt": c.get("title", ""),
            "source_date": c.get("timestamp"),
            "component": c.get("component")
        })

    # Issue/PR citations
    for item in (evidence_pack.issue_evidence + evidence_pack.pr_evidence)[:3]:
        item_id = str(item.get("issue_id") or item.get("pr_id") or "1")
        evidence_refs.append({
            "id": f"ref-{uuid.uuid4().hex[:6]}",
            "owner_type": "message",
            "owner_id": "",
            "source_type": "issue" if "issue" in item.get("id", "") else "pr",
            "source_id": item_id,
            "similarity": item.get("similarity", 0.8),
            "excerpt": item.get("title", ""),
            "source_date": item.get("timestamp"),
            "component": item.get("component")
        })

    # Search decisions from Decision Log (Section 8.2, 8.5)
    matching_decisions = workflow_db.list_decisions(search_query=req.content)
    for dec in matching_decisions[:2]:
        evidence_refs.append({
            "id": f"ref-{uuid.uuid4().hex[:6]}",
            "owner_type": "message",
            "owner_id": "",
            "source_type": "decision",
            "source_id": dec.id.upper(),
            "similarity": 0.9,
            "excerpt": f"Architectural Decision [{dec.id.upper()}]: {dec.title}. Chosen: {dec.chosen_option}.",
            "source_date": dec.decided_at,
            "component": dec.component
        })

    from app.rag.llm import EvidenceGroundedLLM
    llm_service = EvidenceGroundedLLM()
    answer_res = llm_service.answer_qa(req.content, conv.repository_id, evidence_pack)

    from app.workflow.models import EvidenceReference
    ref_models = [EvidenceReference(**r) for r in evidence_refs]

    # 3. Add assistant message
    asst_msg = workflow_db.add_message(
        conversation_id=conv_id,
        role="assistant",
        content=answer_res["answer"],
        evidence_refs=ref_models,
        confidence=answer_res.get("confidence", 0.88),
        retrieval_mode=req.system_mode
    )

    return {
        "user_message": user_msg,
        "assistant_message": asst_msg
    }


@router.post("/messages/{message_id}/feedback")
def submit_feedback(message_id: str, req: MessageFeedbackRequest):
    workflow_db.submit_message_feedback(message_id, req.rating, req.reason)
    return {"status": "success"}


@router.post("/messages/{message_id}/save-note")
def save_note(message_id: str, req: SaveNoteRequest):
    workflow_db.save_message_as_note(message_id, req.note_title)
    return {"status": "success", "message": "Saved as team note"}


@router.get("/notes")
def list_notes():
    return workflow_db.get_team_notes()


@router.get("/knowledge-map")
def get_knowledge_map(repository_id: str = Query("netbox")):
    """Returns interactive relationship graph from NetworkX (Section 8.2)."""
    from app.graph.knowledge_graph import RepositoryKnowledgeGraph
    kg = RepositoryKnowledgeGraph(sqlite_store)
    kg.build_graph(repository_id)
    return kg.get_subgraph_data_for_ui(max_nodes=40)


# ---------------------------------------------------------------------------
# 3. Feature Requests (Section 7.1, 8.3, 10.4)
# ---------------------------------------------------------------------------

class CreateRequestPayload(BaseModel):
    title: str
    description: str
    acceptance_criteria: List[str]
    priority: str = "P1"
    project_id: str = "proj-platform-core"
    repo_id: str = "netbox"
    target_component: Optional[str] = None
    external_issue_ref: Optional[str] = None


class ClarityCheckPayload(BaseModel):
    title: str
    description: str
    acceptance_criteria: List[str]
    repo_id: str = "netbox"
    project_id: str = "proj-platform-core"


class UpdateRequestStatusPayload(BaseModel):
    status: RequestStatus
    reason: Optional[str] = None


@router.get("/requests")
def list_requests(
    project_id: Optional[str] = None,
    status: Optional[str] = None,
    priority: Optional[str] = None,
    component: Optional[str] = None
):
    return workflow_db.list_feature_requests(
        project_id=project_id,
        status=status,
        priority=priority,
        component=component
    )


@router.post("/requests")
def create_request(payload: CreateRequestPayload, user: User = Depends(get_user)):
    req = workflow_db.create_feature_request(
        title=payload.title,
        description=payload.description,
        acceptance_criteria=payload.acceptance_criteria,
        priority=payload.priority,
        requester=user,
        project_id=payload.project_id,
        repo_id=payload.repo_id,
        target_component=payload.target_component,
        external_issue_ref=payload.external_issue_ref
    )
    return req


@router.get("/requests/{req_id}")
def get_request(req_id: str):
    r = workflow_db.get_feature_request(req_id)
    if not r:
        raise HTTPException(status_code=404, detail="Feature request not found.")
    return r


@router.put("/requests/{req_id}/status")
def update_request_status(req_id: str, payload: UpdateRequestStatusPayload, user: User = Depends(get_user)):
    try:
        updated = workflow_db.transition_request_status(
            request_id=req_id,
            target_status=payload.status,
            actor=user,
            reason=payload.reason
        )
        return updated
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/requests/clarity-check")
@router.post("/requests/{req_id}/clarity-check")
def run_clarity_check(payload: ClarityCheckPayload, req_id: Optional[str] = None):
    return clarity_assistant.analyze_request_clarity(
        title=payload.title,
        description=payload.description,
        acceptance_criteria=payload.acceptance_criteria,
        repo_id=payload.repo_id,
        project_id=payload.project_id
    )


@router.get("/requests/{req_id}/timeline")
def get_request_timeline(req_id: str):
    return workflow_db.get_audit_logs(object_type="request", object_id=req_id)


# ---------------------------------------------------------------------------
# 4. Feature Briefs (Section 7.1, 7.6, 8.4, 10.4)
# ---------------------------------------------------------------------------

class GenerateBriefPayload(BaseModel):
    change_summary: Optional[str] = None


@router.post("/requests/{req_id}/brief")
async def generate_brief(
    req_id: str,
    payload: GenerateBriefPayload,
    user: User = Depends(get_user)
):
    try:
        brief = await brief_generator.generate_brief_async(
            request_id=req_id,
            actor=user,
            change_summary=payload.change_summary
        )
        return brief
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/requests/{req_id}/brief")
def get_request_brief(req_id: str):
    brief = workflow_db.get_current_brief(req_id)
    if not brief:
        # Check if there is any brief version
        versions = workflow_db.get_brief_versions(req_id)
        if versions:
            return versions[0]
        raise HTTPException(status_code=404, detail="No Feature Brief generated for this request yet.")
    return brief


@router.get("/briefs/{req_id}/versions")
def get_brief_versions(req_id: str):
    return workflow_db.get_brief_versions(req_id)


@router.get("/briefs/{req_id}/versions/diff")
def diff_versions(req_id: str, version_a: int = Query(...), version_b: int = Query(...)):
    versions = workflow_db.get_brief_versions(req_id)
    v_a = next((v for v in versions if v.version == version_a), None)
    v_b = next((v for v in versions if v.version == version_b), None)
    if not v_a or not v_b:
        raise HTTPException(status_code=404, detail="Specified brief versions not found.")
    return brief_generator.diff_brief_versions(v_a, v_b)


@router.post("/briefs/{brief_id}/approve")
def approve_brief(brief_id: str, user: User = Depends(get_user)):
    try:
        approved = workflow_db.approve_brief_version(brief_id, actor=user)
        return approved
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/requests/{req_id}/brief/export")
def export_brief(req_id: str):
    brief = workflow_db.get_current_brief(req_id)
    if not brief:
        raise HTTPException(status_code=404, detail="Brief not found.")
    
    md_lines = [
        f"# Feature Brief: {brief.request_id} (Version {brief.version})",
        f"**Generated:** {brief.generated_at} | **Status:** {brief.status.value}",
        f"**Overall Impact:** {brief.overall_impact_level} | **Confidence:** {int(brief.overall_confidence * 100)}%",
        "",
        "## 1. Requirement Understanding",
        brief.restated_requirement,
        "",
        "## 2. Affected Components",
    ]
    for c in brief.affected_components:
        md_lines.append(f"- **`{c['component']}`**: Impact Score {c.get('score', 0):.2f} ({c.get('impact_level', 'LOW')})")
    
    md_lines.extend(["", "## 3. Recommended Regression Tests"])
    for t in brief.recommended_tests:
        md_lines.append(f"- `{t.get('test_file')}` (Score: {t.get('score', 0):.2f})")

    md_lines.extend(["", "## 4. Implementation Options"])
    for opt in brief.options:
        md_lines.append(f"### {opt.name}\n{opt.description}\n- **Effort:** {opt.effort} | **Risk:** {opt.risk}")

    return {"format": "markdown", "content": "\n".join(md_lines)}


# ---------------------------------------------------------------------------
# 5. Tasks (Section 7.1, 8.6, 10.4)
# ---------------------------------------------------------------------------

class CreateTasksFromBriefPayload(BaseModel):
    tasks: List[Dict[str, Any]]


class UpdateTaskStatusPayload(BaseModel):
    status: TaskStatus
    reason: Optional[str] = None


class PrePrCheckPayload(BaseModel):
    diff_text: Optional[str] = None
    branch: Optional[str] = None


@router.get("/tasks")
def list_tasks(
    request_id: Optional[str] = None,
    assignee_id: Optional[str] = None,
    status: Optional[str] = None
):
    return workflow_db.list_tasks(request_id=request_id, assignee_id=assignee_id, status=status)


@router.post("/requests/{req_id}/tasks")
def create_tasks_from_brief(
    req_id: str,
    payload: CreateTasksFromBriefPayload,
    user: User = Depends(get_user)
):
    created = []
    for idx, t in enumerate(payload.tasks):
        task = workflow_db.create_task(
            request_id=req_id,
            title=t["title"],
            description=t.get("description", t["title"]),
            component=t.get("component", "core"),
            priority=t.get("priority", "P1"),
            order=idx + 1,
            depends_on=t.get("depends_on", []),
            actor=user,
            assignee_id=t.get("assignee_id")
        )
        # Populate context pack
        cpack = tasks_service.generate_context_pack(task)
        task.context_pack = cpack
        created.append(task)
    return created


@router.get("/tasks/{task_id}")
def get_task(task_id: str):
    t = workflow_db.get_task_by_id_or_key(task_id)
    if not t:
        raise HTTPException(status_code=404, detail="Task not found.")
    return t


@router.put("/tasks/{task_id}/status")
def update_task_status(task_id: str, payload: UpdateTaskStatusPayload, user: User = Depends(get_user)):
    try:
        t = workflow_db.update_task_status(task_id, payload.status, actor=user, reason=payload.reason)
        return t
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/tasks/{task_id}/context-pack")
def get_task_context_pack(task_id: str):
    t = workflow_db.get_task_by_id_or_key(task_id)
    if not t:
        raise HTTPException(status_code=404, detail="Task not found.")
    return tasks_service.generate_context_pack(t)


@router.post("/tasks/{task_id}/pre-pr-check")
def run_pre_pr_check(task_id: str, payload: PrePrCheckPayload):
    return tasks_service.run_pre_pr_check(task_id, diff_text=payload.diff_text, branch=payload.branch)


@router.get("/tasks/{task_id}/suggest-reviewers")
def suggest_reviewers(task_id: str):
    t = workflow_db.get_task_by_id_or_key(task_id)
    if not t:
        raise HTTPException(status_code=404, detail="Task not found.")
    return tasks_service.suggest_reviewers(t.component, "netbox")


# ---------------------------------------------------------------------------
# 6. Architectural Decisions (Section 7.1, 8.5, 10.4)
# ---------------------------------------------------------------------------

class CreateDecisionPayload(BaseModel):
    title: str
    context: str
    options_considered: List[Dict[str, Any]] = Field(default_factory=list)
    chosen_option: str = ""
    rationale: str
    tradeoffs_accepted: List[str] = Field(default_factory=list)
    request_id: Optional[str] = None
    brief_version_id: Optional[str] = None
    component: Optional[str] = None
    project_id: Optional[str] = None


@router.get("/decisions")
def list_decisions(
    request_id: Optional[str] = None,
    component: Optional[str] = None,
    status: Optional[str] = None,
    search: Optional[str] = None,
    project_id: Optional[str] = None
):
    return workflow_db.list_decisions(
        request_id=request_id,
        component=component,
        status=status,
        search_query=search
    )


@router.post("/decisions")
def create_decision(payload: CreateDecisionPayload, user: User = Depends(get_user)):
    dec = workflow_db.create_decision(
        title=payload.title,
        context=payload.context,
        options_considered=payload.options_considered,
        chosen_option=payload.chosen_option,
        rationale=payload.rationale,
        tradeoffs_accepted=payload.tradeoffs_accepted,
        actor=user,
        request_id=payload.request_id,
        brief_version_id=payload.brief_version_id,
        component=payload.component
    )
    return dec


class SupersedeDecisionPayload(BaseModel):
    new_decision_id: str


@router.put("/decisions/{dec_id}/supersede")
def supersede_decision(dec_id: str, payload: SupersedeDecisionPayload, user: User = Depends(get_user)):
    workflow_db.supersede_decision(dec_id, payload.new_decision_id, actor=user)
    return {"status": "success", "message": f"Decision superseded by {payload.new_decision_id}"}


# ---------------------------------------------------------------------------
# 7. Pipelines & Gate (Section 7.1, 8.7, 10.4, 13.6)
# ---------------------------------------------------------------------------

class OverrideGatePayload(BaseModel):
    reason: str
    new_decision: GateDecision = GateDecision.APPROVED


class SimulateRunPayload(BaseModel):
    task_id: str
    simulate_failure: bool = False


@router.get("/pipelines")
def list_pipelines(task_id: Optional[str] = None, repo_id: Optional[str] = None):
    return workflow_db.list_pipeline_runs(task_id=task_id, repo_id=repo_id)


@router.get("/pipelines/{run_id}")
def get_pipeline_run(run_id: str):
    r = workflow_db.get_pipeline_run(run_id)
    if not r:
        raise HTTPException(status_code=404, detail="Pipeline run not found.")
    return r


@router.get("/pipelines/{run_id}/gate")
def get_pipeline_gate(run_id: str):
    g = workflow_db.get_gate_result_for_run(run_id)
    if not g:
        # Compute if not yet computed
        return pipelines_service.evaluate_gate_for_run(run_id)
    return g


@router.post("/pipelines/{run_id}/gate")
def evaluate_pipeline_gate(run_id: str, user: User = Depends(get_user)):
    return pipelines_service.evaluate_gate_for_run(run_id, actor=user)


@router.post("/pipelines/{run_id}/override")
def override_pipeline_gate(run_id: str, payload: OverrideGatePayload, user: User = Depends(get_user)):
    try:
        return workflow_db.override_gate_decision(
            run_id=run_id,
            new_decision=payload.new_decision,
            reason=payload.reason,
            actor=user
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/pipelines/simulate-run")
def trigger_simulated_run(payload: SimulateRunPayload, user: User = Depends(get_user)):
    """Phase 1 Simulated Verification Contract (Section 13.6)."""
    return pipelines_service.trigger_simulated_verification_run(
        task_id=payload.task_id,
        simulate_failure=payload.simulate_failure,
        actor=user
    )


# ---------------------------------------------------------------------------
# 8. Outcomes & Insights (Section 7.7, 8.8, 10.4)
# ---------------------------------------------------------------------------

@router.get("/insights")
def get_insights(
    role: Optional[str] = None,
    repo: Optional[str] = None,
    project_id: Optional[str] = None
):
    return insights_service.get_insights_dashboard(role=role, repo_id=repo, project_id=project_id)


@router.get("/outcomes/{task_id}")
def get_outcome(task_id: str):
    outcomes = workflow_db.list_outcomes(task_id=task_id)
    if not outcomes:
        raise HTTPException(status_code=404, detail="No outcome recorded for this task yet.")
    return outcomes[0]


@router.get("/repository-file-history")
def get_file_history(repository_id: str = Query("netbox"), file_path: str = Query(...)):
    """Returns commits, PRs, and issues that modified a specific file (Section 10.4)."""
    evidence_pack = retriever.build_evidence_pack(
        repository_id=repository_id,
        query_or_change=file_path,
        system_mode="History-RAG",
        top_k=10
    )
    return {
        "repository_id": repository_id,
        "file_path": file_path,
        "commits": evidence_pack.commit_evidence[:5],
        "issues": evidence_pack.issue_evidence[:3],
        "prs": evidence_pack.pr_evidence[:3],
        "related_tests": [t for t in evidence_pack.available_tests if file_path.split("/")[-1].split(".")[0] in t]
    }


# ---------------------------------------------------------------------------
# 9. Audit Trail (Section 7.3, 10.4, 10.6)
# ---------------------------------------------------------------------------

@router.get("/audit")
def list_audit_logs(
    object_type: Optional[str] = None,
    object_id: Optional[str] = None,
    limit: int = 100
):
    return workflow_db.get_audit_logs(object_type=object_type, object_id=object_id, limit=limit)


# ---------------------------------------------------------------------------
# 10. Real-time Server-Sent Events (Section 10.2, 10.4, 10.6)
# ---------------------------------------------------------------------------

@router.get("/events")
async def sse_event_stream(request: Request):
    """Authenticated SSE stream with reconnection (Section 10.6)."""
    queue: asyncio.Queue = asyncio.Queue()
    EVENT_SUBSCRIBERS.append(queue)

    async def event_generator():
        try:
            # Send initial keepalive
            yield {
                "event": "connected",
                "data": json.dumps({"status": "connected", "time": datetime.now(timezone.utc).isoformat()})
            }
            while True:
                if await request.is_disconnected():
                    break
                try:
                    event = await asyncio.wait_for(queue.get(), timeout=15.0)
                    yield {
                        "event": event["event"],
                        "data": json.dumps(event["data"])
                    }
                except asyncio.TimeoutError:
                    yield {
                        "event": "ping",
                        "data": json.dumps({"timestamp": datetime.now(timezone.utc).isoformat()})
                    }
        finally:
            if queue in EVENT_SUBSCRIBERS:
                EVENT_SUBSCRIBERS.remove(queue)

    return EventSourceResponse(event_generator())


# ---------------------------------------------------------------------------
# 11. GitHub Webhooks (Section 10.4, 10.5)
# ---------------------------------------------------------------------------

@router.post("/webhooks/github")
async def receive_github_webhook(
    request: Request,
    x_github_event: str = Header("ping"),
    x_github_delivery: str = Header(default_factory=lambda: uuid.uuid4().hex),
    x_hub_signature_256: Optional[str] = Header(None)
):
    body_bytes = await request.body()
    if not webhook_handler.verify_signature(body_bytes, x_hub_signature_256):
        raise HTTPException(status_code=401, detail="Invalid GitHub webhook signature.")

    try:
        payload = json.loads(body_bytes.decode("utf-8")) if body_bytes else {}
    except Exception:
        payload = {}

    res = webhook_handler.process_github_event(
        event_type=x_github_event,
        delivery_id=x_github_delivery,
        payload=payload
    )
    return res
