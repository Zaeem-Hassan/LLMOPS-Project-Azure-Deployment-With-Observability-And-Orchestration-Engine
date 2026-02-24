import uuid
import json 
import logging
from pprint import pprint
from dotenv import load_dotenv
load_dotenv(override=True)
from backend.src.graph.workflow import app

logger = logging.getLogger("main")  

logger.basicConfig(
    level=logging.INFO,
    format="%(asctime)s-%(levelname)s-%(message)s"
)

logger = logger.getLogger("brand-guardian-runner")

def run_cli_simulations():
    session_id = str(uuid.uuid4())
    logger.info(f"Starting Audit Session: {session_id}")

    initial_state = {
        "video_url" : "",
        "video_id" : f"vid_{session_id[:8]}",
        "compliance_results" : [],
        "errors" : [] 
    }

    print("n-----Initializing workflow----------")
    print(f"Input Payload : {json.dumps(initial_state,indent=2)}")

    try:
        final_state = app.invoke(initial_state)
        print("\n-----Workflow Completed------")


        print("\n Compliance Audit Report ==")
        print(f"Video ID : {final_state.get('video_id')}")
        print(f"Status : {final_state.get('status')}")
        print("\n [Violation  Detected]")
        
        results = final_state.get("compliance_results",[])
       
        if results :
            for issue in results:
                print(f"- [{issue.get('severity')}] [{issue.get('category')}] : [{issue.get('description')}]")
        else : 
            print("No violations detected")
        
        print("\n [FINAL SUMMARY]")
        print(final_state.get('final_report'))

    except Exception as e:
        logger.error(f"Workflow failed: {e}")
        print(f"\n [ERROR] : {e}")

if __name__ == "__main__":
    run_cli_simulations()