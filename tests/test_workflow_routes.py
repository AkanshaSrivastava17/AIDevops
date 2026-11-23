"""
Comprehensive unit & integration tests for the History-RAG Revision 2.2 Workflow Endpoints.
Directly tests all Section 10.4 & 10.8 endpoints, Demo Role Switcher, Clarity, Briefs,
Tasks, Pre-PR check, Decisions, Gate evaluation & overrides, Insights, and Conversations.
"""
import pytest
from app.api.workflow_routes import (
    list_demo_personas, switch_persona, get_current_user_profile,
    SwitchPersonaRequest,
    list_requests, create_request, get_request, CreateRequestPayload,
    run_clarity_check, ClarityCheckPayload,
    get_brief_versions,
    list_tasks, get_task_context_pack, run_pre_pr_check, PrePrCheckPayload,
    list_decisions, create_decision, CreateDecisionPayload,
    list_pipelines, get_pipeline_gate, override_pipeline_gate, OverrideGatePayload,
    get_insights,
    list_conversations, create_conversation, send_conversation_message,
    CreateConversationRequest, SendMessageRequest,
    workflow_db, auth_service
)
from app.workflow.models import User, GlobalRole, ProjectRole


def test_auth_personas_and_switching():
    # 1. List personas
    personas = list_demo_personas()
    assert len(personas) == 6
    roles = {p["role"] for p in personas}
    assert "junior_developer" in roles
    assert "tech_lead" in roles
    assert "product_owner" in roles
    assert "qa_engineer" in roles
    assert "engineering_manager" in roles
    assert "admin" in roles

    # 2. Switch persona
    switch_res = switch_persona(SwitchPersonaRequest(user_id="user-techlead"))
    assert switch_res["status"] == "success"
    assert switch_res["active_persona"]["name"] == "Marcus Vance"
    assert "Tech Lead" in switch_res["active_persona"]["title"]

    # 3. Check get_current_user_profile
    lead_user = auth_service.get_current_user()
    me = get_current_user_profile(user=lead_user)
    assert me["user"]["name"] == "Marcus Vance"


def test_clarity_assistant_analysis():
    payload = ClarityCheckPayload(
        title="Add rate limiting",
        description="We need to make our API fast and rate limit requests so it doesn't break.",
        acceptance_criteria=["Must limit to 100 req/min"],
        project_id="proj-platform-core",
        repository_id="netbox"
    )
    data = run_clarity_check(payload)
    assert "flags" in data
    assert "suggested_criteria" in data
    assert isinstance(data["flags"], list)
    assert isinstance(data["suggested_criteria"], list)


def test_requests_lifecycle():
    po_user = auth_service.switch_demo_persona("user-po")

    # List requests
    reqs = list_requests(project_id="proj-platform-core")
    assert len(reqs) >= 1

    # Create request
    create_payload = CreateRequestPayload(
        title="Support VRF-aware Route Targets Unit Test",
        description="Allow RouteTarget import and export per tenant VRF namespace.",
        acceptance_criteria=["VRF assignment required", "Export route target format valid"],
        project_id="proj-platform-core",
        repository_id="netbox",
        priority="P1"
    )
    new_req = create_request(create_payload, user=po_user)
    assert new_req.title == create_payload.title
    assert new_req.status.value.lower() == "draft"

    # Fetch by ID
    fetched = get_request(new_req.id)
    assert fetched.id == new_req.id


def test_brief_generation_and_versions():
    # Use existing seeded request HR-101
    briefs = get_brief_versions(req_id="HR-101")
    assert len(briefs) >= 1
    v1 = briefs[0]
    assert v1.version >= 1
    assert "components" in v1.impact_analysis
    assert v1.reproducibility is not None


def test_tasks_and_context_pack():
    lead_user = auth_service.switch_demo_persona("user-techlead")

    tasks = list_tasks(request_id="HR-101")
    assert len(tasks) >= 1
    task_id = tasks[0].id

    # Context Pack
    pack = get_task_context_pack(task_id=task_id)
    assert pack.task_description is not None
    assert len(pack.relevant_files) >= 1
    assert len(pack.suggested_reviewers) >= 1

    # Pre-PR Check
    pre_pr_payload = PrePrCheckPayload(
        changed_files=["netbox/ipam/models/vrf.py", "netbox/ipam/api/serializers.py"],
        diff_text="diff --git a/netbox/ipam/models/vrf.py..."
    )
    check = run_pre_pr_check(task_id=task_id, payload=pre_pr_payload)
    assert hasattr(check, "check_passed")
    assert check.scope_drift_detected is not None


def test_decisions_log():
    lead_user = auth_service.switch_demo_persona("user-techlead")

    decisions = list_decisions(project_id="proj-platform-core")
    assert len(decisions) >= 1
    assert any(d.key == "DEC-018" for d in decisions)

    # Create new decision
    dec_payload = CreateDecisionPayload(
        title="Use PostgreSQL JSONB for VRF Extensible Attributes",
        context="We need custom attribute schemas per VRF without altering core table.",
        decision="Store extended VRF metadata in jsonb column with GIN index.",
        rationale="High write efficiency and query flexibility.",
        tradeoffs_accepted=["Slightly increased index storage footprint"],
        project_id="proj-platform-core"
    )
    new_dec = create_decision(dec_payload, user=lead_user)
    assert new_dec.key.startswith("DEC-")


def test_pipelines_and_gate_override():
    qa_user = auth_service.switch_demo_persona("user-qa")

    runs = list_pipelines(repo_id="netbox")
    assert len(runs) >= 1
    run_id = runs[0].id

    # Check Gate
    gate = get_pipeline_gate(run_id=run_id)
    assert gate.decision.value in ["Approved", "Warning", "Blocked"]
    assert gate.freshness.value in ["Current", "Stale"]

    # Override gate (mandatory reason)
    override_payload = OverrideGatePayload(
        reason="QA lead verified VRF boundary test pass in staging manual verification."
    )
    updated_run = override_pipeline_gate(run_id=run_id, payload=override_payload, user=qa_user)
    assert updated_run.decision.value == "Approved"


def test_insights_dashboard():
    insights = get_insights(project_id="proj-platform-core")
    assert "questions" in insights
    assert "early_risk" in insights["questions"]
    assert "role_metrics" in insights
    assert "retrospectives" in insights


def test_conversations_and_qa():
    dev_user = auth_service.switch_demo_persona("user-junior")

    convs = list_conversations(project_id="proj-platform-core", user=dev_user)
    assert isinstance(convs, list)

    # Create conversation
    new_conv = create_conversation(CreateConversationRequest(
        title="VRF implementation details",
        project_id="proj-platform-core",
        repository_id="netbox"
    ), user=dev_user)
    assert new_conv.id is not None

    # Send message
    msg_res = send_conversation_message(
        conv_id=new_conv.id,
        req=SendMessageRequest(
            content="Where is the VRF model defined in NetBox?",
            system_mode="History-RAG"
        ),
        user=dev_user
    )
    assert "assistant_message" in msg_res
    assert msg_res["assistant_message"].content is not None
    assert len(msg_res["assistant_message"].evidence_refs) >= 1
