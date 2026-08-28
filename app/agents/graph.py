import logging
from langgraph.graph import StateGraph, END

from app.agents.state import BridgeScoreState
from app.agents.document_verification import dva_node
from app.agents.income_inference import iia_node
from app.agents.credit_scoring import csa_node
from app.agents.compliance import ca_node
from app.agents.orchestrator import oa_node

logger = logging.getLogger("bridgescore.agents.graph")


def should_skip_to_oa_after_dva(state: BridgeScoreState) -> str:
 
    if state.get("dva_hard_blocks"):
        logger.warning(
            f"DVA hard block detected: {state['dva_hard_blocks']} — "
            f"routing directly to OA"
        )
        return "orchestrator"
    return "income_inference"


def should_skip_to_oa_after_ca(state: BridgeScoreState) -> str:
   
    if not state.get("nrb_compliant", True):
        logger.warning("CA: NRB non-compliant — routing directly to OA")
        return "orchestrator"
    return "orchestrator"


def build_graph() -> StateGraph:
   
    graph = StateGraph(BridgeScoreState)

   
    graph.add_node("document_verification", dva_node)
    graph.add_node("income_inference",      iia_node)
    graph.add_node("credit_scoring",        csa_node)
    graph.add_node("compliance",            ca_node)
    graph.add_node("orchestrator",          oa_node)

    graph.set_entry_point("document_verification")

    graph.add_conditional_edges(
        "document_verification",
        should_skip_to_oa_after_dva,
        {
            "income_inference": "income_inference",
            "orchestrator":     "orchestrator",
        }
    )

    graph.add_edge("income_inference", "credit_scoring")
    graph.add_edge("credit_scoring",   "compliance")

    graph.add_conditional_edges(
        "compliance",
        should_skip_to_oa_after_ca,
        {
            "orchestrator": "orchestrator",
        }
    )

    graph.add_edge("orchestrator", END)

    compiled = graph.compile()
    logger.info("BridgeScore LangGraph pipeline compiled successfully")
    return compiled


pipeline = build_graph()