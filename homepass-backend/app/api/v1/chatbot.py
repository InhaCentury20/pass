from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from pydantic import BaseModel

router = APIRouter(prefix="/chatbot", tags=["chatbot"])

class ChatbotQuery(BaseModel):
    query: str
    context_id: str | None = None

@router.post("/query")
def query_chatbot(
    request: ChatbotQuery,
    db: Session = Depends(get_db)
):
    """
    AI 챗봇에게 질문하기 (RAG 기반)
    
    - query: 사용자 질문
    - context_id: 대화 컨텍스트 ID (선택사항)
    
    TODO: RAG 구현 필요
    """
    # TODO: RAG 기반 답변 생성 로직 구현
    return {
        "message": "AI 챗봇 API (구현 예정)",
        "query": request.query,
        "response": "RAG 기반 답변이 여기에 표시됩니다."
    }

