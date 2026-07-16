from app.agent.routing import AgentRouter, RouteDecision


def test_keyword_routes_cover_management_domains():
    router = AgentRouter()

    assert router.route("查看当前数据集版本").agent == "dataset"
    assert router.route("最近训练到第几轮了").agent == "training"
    assert router.route("查询可乐的价格").agent == "catalog"
    assert router.route("检测这张商品图").agent == "detection"


def test_attachment_always_routes_to_detection():
    decision = AgentRouter().route("帮我处理一下", has_attachments=True)

    assert decision.agent == "detection"
    assert decision.method == "attachment"
    assert decision.confidence == 1.0


def test_dataset_conversation_keeps_attachment_in_dataset_agent():
    decision = AgentRouter().route(
        "我把样品图发来了",
        has_attachments=True,
        preferred_agent="dataset",
    )

    assert decision.agent == "dataset"
    assert decision.method == "conversation_context"


def test_active_dataset_handoff_keeps_attachment_in_dataset_agent():
    decision = AgentRouter().route(
        "继续处理",
        has_attachments=True,
        active_workflow_agent="dataset",
    )

    assert decision.agent == "dataset"
    assert decision.method == "active_workflow"


def test_explicit_detection_request_overrides_dataset_context():
    decision = AgentRouter().route(
        "请检测这张图片",
        has_attachments=True,
        preferred_agent="dataset",
        active_workflow_agent="dataset",
    )

    assert decision.agent == "detection"
    assert decision.method == "attachment_intent"


def test_dataset_field_reply_keeps_conversation_context():
    decision = AgentRouter().route(
        "商品名称可乐，类别英文名 cola，价格 3.5 元",
        preferred_agent="dataset",
    )

    assert decision.agent == "dataset"
    assert decision.method == "conversation_context"


def test_ambiguous_message_uses_embedding_route(monkeypatch):
    expected = RouteDecision("dataset", "embedding", 0.83, "test")
    monkeypatch.setattr(AgentRouter, "_embedding_route", lambda self, message: expected)

    assert AgentRouter().route("帮我处理一下新一批资料") == expected


def test_ambiguous_message_falls_back_to_knowledge(monkeypatch):
    monkeypatch.setattr(AgentRouter, "_embedding_route", lambda self, message: None)

    decision = AgentRouter().route("你好")

    assert decision.agent == "knowledge"
    assert decision.method == "fallback"
