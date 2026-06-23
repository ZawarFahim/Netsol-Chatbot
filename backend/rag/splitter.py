from langchain_text_splitters import RecursiveCharacterTextSplitter

def split_documents(docs):
    return RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200).split_documents(docs)