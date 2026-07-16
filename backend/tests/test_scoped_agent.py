import pytest

from app.agent.scoped_agent import ScopedToolAgent


class _FakeExecutor:
    async def astream_events(self, payload, version):
        yield {
            "event": "on_tool_end",
            "name": "prepare_add_samples_handoff",
            "data": {
                "output": (
                    '{"handoff_uuid":"handoff-1","page_url":"/datasets?handoff_id=handoff-1",'
                    '"status":"ready_for_handoff","context":{"dataset_id":7}}'
                )
            },
        }


class _FakeConfirmationExecutor:
    async def astream_events(self, payload, version):
        yield {
            "event": "on_tool_end",
            "name": "preview_update_product_price",
            "data": {
                "output": (
                    '{"operation_uuid":"operation-1","status":"pending","risk_level":"R2",'
                    '"confirmation_token":"secret-token","impact":{"title":"更新商品价格"}}'
                )
            },
        }


@pytest.mark.asyncio
async def test_dataset_handoff_tool_emits_structured_event():
    agent = ScopedToolAgent.__new__(ScopedToolAgent)
    agent.name = "dataset"
    agent.executor = _FakeExecutor()

    events = [event async for event in agent.stream("继续")]

    handoff = next(event for event in events if event["type"] == "handoff_required")
    assert handoff["agent"] == "dataset"
    assert handoff["handoff_id"] == "handoff-1"
    assert handoff["page_url"].endswith("handoff-1")
    assert handoff["context"]["dataset_id"] == 7


@pytest.mark.asyncio
async def test_preview_tool_emits_confirmation_required_event():
    agent = ScopedToolAgent.__new__(ScopedToolAgent)
    agent.name = "catalog"
    agent.executor = _FakeConfirmationExecutor()

    events = [event async for event in agent.stream("把价格改为 4.2")]

    confirmation = next(
        event for event in events if event["type"] == "confirmation_required"
    )
    assert confirmation["agent"] == "catalog"
    assert confirmation["operation"]["operation_uuid"] == "operation-1"
    assert confirmation["operation"]["confirmation_token"] == "secret-token"
