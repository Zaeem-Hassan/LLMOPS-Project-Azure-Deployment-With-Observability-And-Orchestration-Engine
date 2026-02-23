import json
import os
import logging
import re
from typing import Dict ,Any,List

from langchain_openai import AzureChatOpenAI, AzureOpenAIEmbeddings
from langchain_community.vectorstores import AzureSearch
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import SystemMessage,HumanMessage

from backend.src.graph.state import VideoAuditState, ComplianceIssue

from backend.src.services.video_indexer import VideoIndexerService

logger = logging.getLogger("brand-guardian")
logging.basicConfig(level)


def index_video_node(state:VideoAuditState) -> Dict[str,Any]:
    video_url = state.get("video_url")
    video_id_input = state.get("video_id","vid_demo")
    
    logger.info(f"Starting video indexing for {video_url}")

    local_filename = "temp_audit_video.mp4"

    try:
        vi_service = VideoIndexerService()
        if "youtube.com" in video_url or "youtu.be" in video_url:
            local_path = vi_service.download_video(video_url,local_filename)
        else :
            raise Exception("Please provide a valid youtube url")
        azure_video_id = vi_service.upload_and_index(local_path,video_id_input)
        logger.info(f"Upload Success {azure_video_id}")
        
        if os.path.exists(local_path):
            os.remove(local_path)
        raw_insights = vi_service.wait_for_processing(azure_video_id)

        clean_data = vi_service.extract_data(raw_insights)
        logger.info("Extraction Complete")
        return clean_data
    except Exception as e : 
        logger.error(f"Error in video indexing: {str(e)}")
        return {
            "errors" : [str(e)],
            "final_status" : "Fail",
            "transcript" : "",
            "ocr_text": []
        }

def audio_content_node(state:VideoAudioState) -> Dict[str,Any]:
    logger.info("[Node:Auditor] querying Knowledge Base")
    transcript = state.get("transcript","")
    if not transcript:
        logger.warning("[Node:Auditor] No transcript found")
        return {
            "final_status" : "Fail",
            "final_report" : "No transcript available for analysis" 
        }
    
    llm = AzureChatOpenAI(
        azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
        azure_deployment=os.getenv("AZURE_OPENAI_CHAT_DEPLOYMENT"),
        api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
        api_key=os.getenv("AZURE_OPENAI_API_KEY"),
        temperature=0.0
    )

    embeddings = AzureOpenAIEmbeddings(
        azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
        azure_deployment=os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT"),
        api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
        api_key=os.getenv("AZURE_OPENAI_API_KEY")
    )

    search_client = AzureSearch(
        endpoint=os.getenv("AZURE_SEARCH_ENDPOINT"),
        api_key=os.getenv("AZURE_SEARCH_API_KEY"),
        index_name=os.getenv("AZURE_SEARCH_INDEX_NAME"),
        embedding_function=embeddings.embed_query
    )

    ocr_text = state.get("ocr_text",[])
    query_text = f"{transcript}{"".join(ocr_text)}"
    docs = vector_store.similarity_search(query_text,k=5)
    retrieved_context = "\n".join([doc.page_content for doc in docs])
    system_prompt = f"""You are a senior brand compliance auditor
    OFFICIAL REGULATORY RULES:
    {retrieved_context}
    INTRUCTIONS:
    1. Analyze the video transcript and ocr text
    2. Identify any violations of the rules
    3. Return stricly JSON in the following format:
    {{
        {
  "compliance_results": [
    {
      "category": "Claim Validation",
      "severity": "CRITICAL",
      "description": "Explanation of the violation..."
    }
  ],
  "status": "FAIL",
  "final_report": "Summary of findings..."
    }
    }}

    If no violations are found , set "status" to "PASS" and "compliance_results" to []
    """

    user_message = f"""
    VIDEO_METADATA : {state.get('video_metadata',{})}
    TRANSCRIPT : {transcript}
    OCR_TEXT : {ocr_text}
    """
    try:
        response = llm.invoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_message)
        ])
        content = response.content

        if "```" in content:
            content = re.search("```json(.*?)```",content,re.DOTALL).group(1)
        audit_data = json.loads(content.strip())
        return{
            "compliance_results" : audit_data.get("compliance_results",[]),
            "final_status" : audit_data.get("status","FAIL"),
            "final_report" : audit_data.get("final_report","")
        }
    
    except Exception as e :
        logger.error(f"System Error in Auditor Node :{str(e)} ")
        logger.error(f"Raw LLM response : {response.content if 'reponse' in locals() else 'None'}")

        return {
            "errors": [str(e)],
            "final_status" : "FAIL"
        }