from typing import Any, Callable

from langgraph.graph import END, START, StateGraph

from app.schemas.analysis_graph_schema import ShoppingAnalysisRequest, ShoppingAnalysisResponse
from app.services.graph.debug import _print_graph_debug, _print_graph_error
from app.services.graph.nodes.filter_node import _text_filter_node
from app.services.graph.nodes.judge_node import _final_formatter_node, _result_judge_node
from app.services.graph.nodes.ocr_node import _ocr_analyzer_node
from app.services.graph.nodes.query_node import _query_generator_node, _retry_query_generator_node
from app.services.graph.nodes.rerank_node import _visual_reranker_node
from app.services.graph.nodes.search_node import _google_search_node, _naver_search_node, _search_identifier_node
from app.services.graph.nodes.visual_node import _frame_synthesizer_node, _visual_feature_analyzer_node
from app.services.graph.state import ShoppingAnalysisState


def analyze_shopping(request: ShoppingAnalysisRequest) -> ShoppingAnalysisResponse:
    initial_state: ShoppingAnalysisState = {
        "request": request,
        "retry_count": 0,
        "tried_queries": [],
        "best_candidates": [],
    }
    _print_graph_debug("START", {"request": request})
    try:
        result = _analysis_graph.invoke(initial_state)
        response = result["response"]
        _print_graph_debug("END", {"response": response})
        return response
    except Exception as exc:
        _print_graph_error("FAILED", exc)
        raise


def _route_after_judge(state: ShoppingAnalysisState) -> str:
    quality = state["quality"]
    max_retries = state["request"].max_retries

    if quality.is_good or state.get("retry_count", 0) >= max_retries:
        next_node = "final_formatter"
    else:
        next_node = "retry_query_generator"

    _print_graph_debug("result_judge.route", {
        "next_node": next_node,
        "is_good": quality.is_good,
        "retry_count": state.get("retry_count", 0),
        "max_retries": max_retries,
        "quality": quality,
    })
    return next_node


def _build_graph():
    workflow = StateGraph(ShoppingAnalysisState)
    workflow.add_node("ocr_analyzer", _with_node_logging("ocr_analyzer", _ocr_analyzer_node))
    workflow.add_node("visual_feature_analyzer", _with_node_logging("visual_feature_analyzer", _visual_feature_analyzer_node))
    workflow.add_node("frame_synthesizer", _with_node_logging("frame_synthesizer", _frame_synthesizer_node))
    workflow.add_node("query_generator", _with_node_logging("query_generator", _query_generator_node))
    workflow.add_node("naver_search", _with_node_logging("naver_search", _naver_search_node))
    workflow.add_node("google_search", _with_node_logging("google_search", _google_search_node))
    workflow.add_node("search_identifier", _with_node_logging("search_identifier", _search_identifier_node))
    workflow.add_node("text_filter", _with_node_logging("text_filter", _text_filter_node))
    workflow.add_node("visual_reranker", _with_node_logging("visual_reranker", _visual_reranker_node))
    workflow.add_node("result_judge", _with_node_logging("result_judge", _result_judge_node))
    workflow.add_node("retry_query_generator", _with_node_logging("retry_query_generator", _retry_query_generator_node))
    workflow.add_node("final_formatter", _with_node_logging("final_formatter", _final_formatter_node))

    workflow.add_edge(START, "ocr_analyzer")
    workflow.add_edge("ocr_analyzer", "visual_feature_analyzer")
    workflow.add_edge("visual_feature_analyzer", "frame_synthesizer")
    workflow.add_edge("frame_synthesizer", "query_generator")
    workflow.add_edge("query_generator", "naver_search")
    workflow.add_edge("naver_search", "google_search")
    workflow.add_edge("google_search", "search_identifier")
    workflow.add_edge("search_identifier", "text_filter")
    workflow.add_edge("text_filter", "visual_reranker")
    workflow.add_edge("visual_reranker", "result_judge")
    workflow.add_conditional_edges(
        "result_judge",
        _route_after_judge,
        {
            "final_formatter": "final_formatter",
            "retry_query_generator": "retry_query_generator",
        },
    )
    workflow.add_edge("retry_query_generator", "naver_search")
    workflow.add_edge("final_formatter", END)

    return workflow.compile()


def _with_node_logging(
    node_name: str,
    node_func: Callable[[ShoppingAnalysisState], dict[str, Any]],
) -> Callable[[ShoppingAnalysisState], dict[str, Any]]:
    def wrapped_node(state: ShoppingAnalysisState) -> dict[str, Any]:
        try:
            result = node_func(state)
            _print_graph_debug(node_name, result)
            return result
        except Exception as exc:
            _print_graph_error(node_name, exc)
            raise

    return wrapped_node



_analysis_graph = _build_graph()
