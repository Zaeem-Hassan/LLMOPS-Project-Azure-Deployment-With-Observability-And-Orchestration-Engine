import os
import time     
import logging
import requests
import yt_dlp
from azure.identity import DefaultAzureCredential

logger = logging.getLogger("video-indexer")

class VideoIndexerService:
    def __init__(self):
        self.credential = DefaultAzureCredential()
        self.subscription_id = os.getenv("AZURE_SUBSCRIPTION_ID")
        self.resource_group_name = os.getenv("AZURE_RESOURCE_GROUP")
        self.AZURE_VI_NAME = os.getenv("AZURE_VI_NAME")
        self.location = os.getenv("AZURE_VI_LOCATION")
        self.api_key = os.getenv("AZURE_VI_API_KEY")

    def get_access_token(self):
        try:
            token_object = self.credential.get_token("https://management.azure.com/.default")
            access_token = token_object.token
            return access_token
        except Exception as e:
            logger.error(f"Error getting access token: {e}")
            raise
    
    def get_account_tokken(self,arm_access_token):
        url = (
    f"https://management.azure.com/subscriptions/{self.subscription_id}"
    f"/resourceGroups/{self.resource_group}"
    f"/providers/Microsoft.VideoIndexer/accounts/{self.AZURE_VI_NAME}"
    f"/generateAccessToken?api-version=2024-01-01"
)

        headers = {"Authorization" : f"Bearer {arm_access_token}"}
        payload = {"permissionType" : "Contributor" , "scope" : "Account"}
        response = requests.post(url, headers=headers , json=payload)
        if response.status_code == 200:
            return response.json().get("accessToken")
        else:
            logger.error(f"Error getting account token: {response.json()}")
            raise
    
    def download_youtube_video(self,youtube_url,output_path="temp_video.mp4"):
        logger.info(f"Downloading video from {youtube_url}")

        ydl_opts = {
            "format": "best[ext=mp4]",
            "outtmpl": output_path,
            "quit" : True,
            "overwrites_output": True,

        }
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([youtube_url])
        except Exception as e:
            logger.error(f"Error downloading video: {e}")
            raise
    
    def upload_video(self,video_path,video_name):
        arm_token = self.get_access_token()
        vi_token = self.get_account_tokken(arm_token)

        api_url = f"https://api.video.ai/{self.location}/Accounts/{self.AZURE_VI_NAME}/Videos"
        parms = {
            "accessToken" : vi_token,
            "name" : video_name,
            "indexingPreset" : "Default",
            "privacy" : "Private",
           
        }

        logger.info(f"Uploading video {video_name} to Video Indexer")

        with open(video_path,"rb") as video_file:
            files = {"file" : video_file}
            response = requests.post(api_url, params=parms, files=files)
            if response.status_code == 200:
                logger.info(f"Video {video_name} uploaded successfully")
                return response.json().get("id")
            else:
                logger.error(f"Error uploading video {video_name}: {response.json()}")
                raise

    def wait_for_processing(self,video_id):
        logger.info(f"Waiting for video {video_id} to be processed")
        while True:
            arm_token  = self.get_access_token()
            vi_token = self.get_account_tokken(arm_token)

            api_url = f"https://api.video.ai/{self.location}/Accounts/{self.AZURE_VI_NAME}/Videos/{video_id}"
            params = {
                "accessToken" : vi_token,
            }
            response = requests.get(url,params=params)
            data  = response.json()
            
            state = data.get("state")
            if state == "Processed":
                logger.info(f"Video {video_id} processed successfully")
                return data
            elif state == "Failed":
                logger.error(f"Video {video_id} processing failed: {data.get('error')}")
                raise Exception(f"Video {video_id} processing failed: {data.get('error')}")
            elif state == " Qurantined":
                raise Exception(f"Video {video_id} is quarantined")

            logger.info(f"Video {video_id} is in state {state}")
            time.sleep(30)

    def extract_data(self,vi_json):
        transcript_lines = []
        for v in vi.json.get("videos",[]):
            for insight in v.get("insights",{}).get("transcript",[]):
                transcrpit_lines.append(insight.get("text"))
        
        ocr_lines = []
        for v in vi.json.get("videos",[]):
            for insight in v.get("insights",{}).get("ocr",[]):
                ocr_lines.append(insight.get("text"))

        return {
            "transcript" : "\n".join(transcript_lines),
            "ocr" : (ocr_lines),
            "video_metadata": {
                "duration" : vi_json.get("summarizedInsights",{}).get("duration"),
                "platform" :"youtube"
            }
        }
        