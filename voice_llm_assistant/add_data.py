from sentence_transformers import SentenceTransformer
import chromadb

embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
client = chromadb.Client()
collection = client.get_or_create_collection("kb")

def add_document(content: str, source: str, metadata: dict = {}):
    embedding = embedding_model.encode(content).tolist()
    collection.add(documents=[content], metadatas=[{"source": source, **metadata}], embeddings=[embedding])

if __name__ == "__main__":
    add_document("Few-shot learning is a technique in ML...", "AI Fundamentals, page 45")
    add_document("Vector search is used for similarity...", "ML Basics, Chapter 7")
    print("Documents added!")
