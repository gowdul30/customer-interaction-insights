import os
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate
from services.vector_store import VectorStoreService

class ChatService:
    def __init__(self, analytics_service=None):
        self.analytics = analytics_service
        
        # Initialize vector store (uses local HuggingFace embeddings)
        try:
            self.vector_store = VectorStoreService()
        except Exception as e:
            print(f"[WARN] VectorStore init failed: {e}. Chat will use fallback.")
            self.vector_store = None
        
        # Initialize LLM for RAG responses
        api_key = os.environ.get("GEMINI_API_KEY")
        if api_key:
            self.llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", google_api_key=api_key)
        else:
            self.llm = None
            print("[WARN] GEMINI_API_KEY not set. RAG chat will be unavailable.")

    def _detect_client(self, message):
        msg = message.lower()
        for client in ["verizon", "wells fargo", "at&t", "att", "comcast", "t-mobile", "tmobile"]:
            if client in msg:
                mapping = {"att": "AT&T", "tmobile": "T-Mobile", "wells fargo": "Wells Fargo"}
                return mapping.get(client, client.title())
        return None

    async def chat(self, message: str, client: str = None):
        detected_client = self._detect_client(message) or client
        
        # Guard: Check both LLM and VectorStore are available
        if not self.llm:
            return "AI Chat is unavailable. Please set GEMINI_API_KEY in your .env file."
        if not self.vector_store or not self.vector_store.embeddings:
            return "Vector database is not initialized. Run `python scripts/seed_vectordb.py` to populate it."

        # Build retriever with optional client filter
        search_kwargs = {"k": 10}
        if detected_client and detected_client.lower() != "all":
            search_kwargs["filter"] = {"client": detected_client}
            
        retriever = self.vector_store.vectorstore.as_retriever(search_kwargs=search_kwargs)

        system_prompt = (
            "You are an AI analytics assistant for a Customer Interaction Insights platform. "
            "You have access to historical customer service calls via semantic search.\n\n"
            "Answer the user's question using ONLY the retrieved call contexts below. "
            "Be specific, cite actual calls or metadata when possible, and include actionable recommendations. "
            "If you cannot answer the question from the context, say so gracefully.\n\n"
            "Context:\n{context}"
        )

        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("human", "{input}"),
        ])

        question_answer_chain = create_stuff_documents_chain(self.llm, prompt)
        rag_chain = create_retrieval_chain(retriever, question_answer_chain)

        try:
            response = rag_chain.invoke(
                {"input": message},
                config={"run_name": f"RAG-Chat-{detected_client or 'general'}"}
            )
            return response["answer"]
        except Exception as e:
            print(f"RAG Error: {e}")
            return f"An error occurred while searching historical calls: {e}"
