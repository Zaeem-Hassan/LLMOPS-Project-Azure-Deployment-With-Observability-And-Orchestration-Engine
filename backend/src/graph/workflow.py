from langgraph.graph import END, StateGraph
from backend.src.graph.state import VideoAuditState

from backend.src.graph.nodes import(
    index_video_node,
    audit_content_node
)

def create_graph():
    

    workflow = StateGraph(VideoAuditState)

    workflow.add_node("indexor",index_video_node)
    workflow.add_node("auditor",audit_content_node)

    workflow.set_entry_point("indexor")

    workflow.add_edge("indexor","auditor")

    workflow.add_edge("auditor",END)

    app = workflow.compile()
    return app

app  = create_graph()