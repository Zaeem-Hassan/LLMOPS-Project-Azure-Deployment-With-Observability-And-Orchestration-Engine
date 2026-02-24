import operator
from typing import Annotated , List , Dict ,Optional ,Any ,TypedDict

class ComplianceIssue(TypedDict):
    category : str
    description : str
    severity : str 
    timestamp : Optional[str]

class VideoAuditState(TypedDict):
    video_url : str 
    video_id :str

    local_file_path : Optional[str] 
    video_metadata :Dict[str,Any] # { "duration" : 120 , "frame_rate" : 30}
    transcript : Optional[str] # raw transcript from video indexer
    ocr_text : Optional[str] # raw ocr text from video indexer
    

    compliance_results : Annotated[List[ComplianceIssue],operator.add]
    

    final_status  : str 
    final_report : str

    errors : Annotated[List[str],operator.add]