"""Deterministic-first, embedding-assisted routing for management agents."""

from __future__ import annotations

from dataclasses import asdict, dataclass

from app.config.settings import settings
from app.core.logger import get_logger
from app.embeddings import DashScopeEmbeddingClient
from app.vectorstore import ChromaStore

logger = get_logger(__name__)

AGENT_NAMES = {"detection", "dataset", "training", "catalog", "knowledge"}

ROUTE_KEYWORDS: dict[str, tuple[str, ...]] = {
    "detection": (
        "检测", "识别", "图片", "视频", "置信度", "漏检", "误检", "推理", "盘点",
    ),
    "dataset": (
        "数据集", "版本", "草稿", "派生", "冻结", "归档", "样品", "样本", "标注", "检测框",
    ),
    "training": (
        "训练", "epoch", "loss", "map", "precision", "recall", "模型", "评估", "日志",
    ),
    "catalog": (
        "价格", "价目", "单价", "商品目录", "sku", "条码", "未定价", "改价",
    ),
}

ROUTE_EXAMPLES: dict[str, tuple[str, ...]] = {
    "detection": (
        "检测这张商品图片", "用当前模型测试一段视频", "为什么这张图出现漏检", "调高置信度再识别",
    ),
    "dataset": (
        "查看当前数据集版本", "从冻结版本派生一个草稿", "给数据集添加新商品样品", "归档旧数据集版本",
    ),
    "training": (
        "查看最近训练任务进度", "分析模型的 mAP 和 Recall", "查看训练日志", "比较两个训练模型",
    ),
    "catalog": (
        "查看当前价目表", "哪些商品还没有价格", "把这个商品价格改为十元", "按条码查询商品单价",
    ),
    "knowledge": (
        "这个平台应该怎么操作", "解释一个系统概念", "查询故障处理手册", "根据知识库回答问题",
    ),
}


@dataclass(frozen=True)
class RouteDecision:
    agent: str
    method: str
    confidence: float
    reason: str

    def event(self) -> dict:
        return {"type": "routing", **asdict(self)}


class AgentRouter:
    COLLECTION = "visionpay_agent_routes"

    @staticmethod
    def _keyword_route(message: str) -> RouteDecision | None:
        lowered = message.lower()
        scores = {
            agent: sum(1 for keyword in keywords if keyword.lower() in lowered)
            for agent, keywords in ROUTE_KEYWORDS.items()
        }
        best_score = max(scores.values(), default=0)
        winners = [agent for agent, score in scores.items() if score == best_score and score > 0]
        if len(winners) != 1:
            return None
        winner = winners[0]
        confidence = min(0.98, 0.72 + best_score * 0.08)
        return RouteDecision(winner, "keyword", confidence, f"命中 {best_score} 个领域关键词")

    def _ensure_examples(
        self, store: ChromaStore, embedding: DashScopeEmbeddingClient
    ) -> None:
        expected = sum(len(items) for items in ROUTE_EXAMPLES.values())
        if store.count >= expected:
            return
        ids: list[str] = []
        documents: list[str] = []
        metadatas: list[dict] = []
        for agent, examples in ROUTE_EXAMPLES.items():
            for index, example in enumerate(examples):
                ids.append(f"route-{agent}-{index}")
                documents.append(example)
                metadatas.append({"agent": agent, "kind": "route_example"})
        store.upsert(
            ids=ids,
            documents=documents,
            embeddings=embedding.embed_documents(documents),
            metadatas=metadatas,
        )

    def _embedding_route(self, message: str) -> RouteDecision | None:
        try:
            embedding = DashScopeEmbeddingClient()
            store = ChromaStore(self.COLLECTION)
            self._ensure_examples(store, embedding)
            results = store.query(embedding=embedding.embed_query(message), top_k=3)
        except Exception as exc:  # noqa: BLE001 - routing must degrade safely
            logger.warning("向量路由不可用，降级到默认路由: %s", exc)
            return None
        votes: dict[str, float] = {}
        for item in results:
            agent = str(item["metadata"].get("agent") or "")
            if agent in AGENT_NAMES:
                votes[agent] = votes.get(agent, 0.0) + max(0.0, item["similarity"])
        if not votes:
            return None
        agent = max(votes, key=votes.get)
        best = next(
            (item for item in results if item["metadata"].get("agent") == agent),
            None,
        )
        similarity = float(best["similarity"] if best else 0.0)
        if similarity < float(settings.ROUTER_MIN_SIMILARITY):
            return None
        return RouteDecision(agent, "embedding", similarity, "DashScope + Chroma 模糊路由")

    @staticmethod
    def _explicit_detection_intent(message: str) -> bool:
        lowered = message.lower()
        return any(
            phrase in lowered
            for phrase in (
                "检测这张", "检测附件", "识别这张", "识别附件", "商品检测",
                "开始检测", "开始识别", "用模型检测", "推理这张",
            )
        )

    def route(
        self,
        message: str,
        *,
        has_attachments: bool = False,
        preferred_agent: str | None = None,
        active_workflow_agent: str | None = None,
    ) -> RouteDecision:
        preferred = preferred_agent if preferred_agent in AGENT_NAMES else None
        active = active_workflow_agent if active_workflow_agent in AGENT_NAMES else None
        explicit_detection = self._explicit_detection_intent(message)

        if has_attachments:
            if explicit_detection:
                return RouteDecision("detection", "attachment_intent", 1.0, "用户明确要求检测附件")
            if active:
                return RouteDecision(active, "active_workflow", 0.99, "附件延续未完成的领域工作流")
            if preferred:
                return RouteDecision(preferred, "conversation_context", 0.96, "附件延续上一领域对话")
            return RouteDecision("detection", "attachment", 1.0, "本轮包含检测附件")

        if preferred == "dataset" and any(
            cue in message.lower()
            for cue in ("商品名", "商品名称", "类别名", "类别英文名", "class_name", "train_new", "train_existing")
        ):
            return RouteDecision("dataset", "conversation_context", 0.96, "继续补充数据集样品字段")

        keyword = self._keyword_route(message)
        if keyword:
            return keyword
        if active:
            return RouteDecision(active, "active_workflow", 0.94, "继续未完成的领域工作流")
        if preferred:
            return RouteDecision(preferred, "conversation_context", 0.86, "延续上一领域对话")
        embedded = self._embedding_route(message)
        if embedded:
            return embedded
        return RouteDecision("knowledge", "fallback", 0.35, "未识别明确业务域，交由知识 Agent 澄清")
