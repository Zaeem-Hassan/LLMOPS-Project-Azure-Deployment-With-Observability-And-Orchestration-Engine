import os
import glob
import logging  
from dotenv import load_dotenv
load_dotenv(override=True)

from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

from langchain_openai import AzureOpenAIEmbeddings
from langchain_community.vectorstores import AzureSearch

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s-%(levelname)s-%(message)s"
)
logger = logging.getLogger("indexer")

def index_docs():
    current_dir  = os.path.dirname(os.path.abspath(__file__))
    data_folder = os.path.join(current_dir,"../../backend/data")


    logger.info("="*60)
    logger.info("Environment Configuration Check: ")
    logger.info(f"Azure Search Endpoint: {os.getenv('AZURE_SEARCH_ENDPOINT')}")
    logger.info(f"Azure Search API Key: {os.getenv('AZURE_SEARCH_API_KEY')}")
    logger.info(f"Azure Search Index Name: {os.getenv('AZURE_SEARCH_INDEX_NAME')}")
    logger.info(f"Azure OpenAI API Key: {os.getenv('AZURE_OPENAI_API_KEY')}")
    logger.info(f"Azure OpenAI API Version: {os.getenv('AZURE_OPENAI_API_VERSION')}")
    logger.info(f"Azure OpenAI API Type: {os.getenv('AZURE_OPENAI_API_TYPE')}")
    logger.info(f"Azure OpenAI API Base: {os.getenv('AZURE_OPENAI_API_BASE')}")
    logger.info(f"Azure OpenAI API Model: {os.getenv('AZURE_OPENAI_API_MODEL')}")
    logger.info(f"Azure OpenAI Endpoint: {os.getenv('AZURE_OPENAI_ENDPOINT')}")
    logger.info("="*60)
    logger.info("Environment Configuration Check: ")
    logger.info(f"Azure Search Endpoint: {os.getenv('AZURE_SEARCH_ENDPOINT')}")


    required_vars = [
        "AZURE_SEARCH_ENDPOINT",
        "AZURE_SEARCH_API_KEY",
        "AZURE_SEARCH_INDEX_NAME",
        "AZURE_OPENAI_API_KEY",
        "AZURE_OPENAI_ENDPOINT"
    ]

    missing_vars  = [var for var in required_vars if not os.getenv(var)]
    if missing_vars:
        logger.error(f"Missing environment variables: {missing_vars}")

    try:
        logger.info("Initializing Azure Open AI Embeddings ....")
        embeddings = AzureOpenAIEmbeddings(
            azure_deployment = os.getenv("AZURE_OPENAI_API_EMBEDDING_DEPLOYMENT"),
            azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT"),
            azure_api_key = os.getenv("AZURE_OPENAI_API_KEY"),
            azure_api_version = os.getenv("AZURE_OPENAI_API_VERSION","2024-02-01"),
        )
        logger.info("Embeddings model initialized ")
    except Exception as e:
        logger.error(f"Error initializing embeddings: {e}")
        return

    try:
        logger.info("Initializing Azure vector store ....")
        vector_store = AzureSearch(
            azure_search_endpoint = os.getenv("AZURE_SEARCH_ENDPOINT"),
            azure_search_key = os.getenv("AZURE_SEARCH_API_KEY"), 
            azure_search_index_name = os.getenv("AZURE_SEARCH_INDEX_NAME"),
            azure_openai_embedding = embeddings.embed_query,
        )
        logger.info("Vector store initialized ")
    except Exception as e:
        logger.error(f"Error initializing vector store: {e}")
        return
    
    pdf_files = glob.glob(os.path.join(data_folder, "*.pdf"))
    if not pdf_files:
        logger.error("No PDF files found in the data folder")
        return
    logger.info(f"Found {len(pdf_files)} PDF files in the data folder")
    
    all_splits = []

    for pdf_path in pdf_files:
        try:
            logger.info(f"Processing {pdf_path}")
            loader = PyPDFLoader(pdf_path)
            documents = loader.load()
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size = 1000,
                chunk_overlap = 200,
                length_function = len,
                is_separator_regex = False,
            )
            splits = text_splitter.split_documents(documents)
            for split in splits:
                split.metadata["source"] = os.path.basename(pdf_path)
                all_splits.extend(split)
            logger.info(f"Split into {len(splits)} chunks for {pdf_path}")
        except Exception as e:
            logger.error(f"Error processing {pdf_path}: {e}")
        
        if all_splits:
            logger.info(f"Uploading {len(all_splits)} documents to Azure Search")

            try:
                vector_store.add_documents(all_splits)
                logger.info("Documents uploaded successfully")
            except Exception as e:
                logger.error(f"Error uploading documents to Azure Search: {e}")
        else:
            logger.info("No documents to upload")
    

if __name__ == "__main__":
    index_docs()