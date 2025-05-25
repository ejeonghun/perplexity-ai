from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import Dict, Optional
from perplexity_async.client import Client
import asyncio
import logging
from contextlib import asynccontextmanager
from cookie import get_perplexity_cookies
from utils import extract_clean_answer, convert_to_plain_text, is_complete_response

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 전역 Client 변수
global_client = None

# 쿠키 유효성 확인 및 클라이언트 초기화 함수
async def initialize_client():
    global global_client
    
    logger.info("브라우저에서 Perplexity 쿠키 가져오기 시도 중...")
    cookies = get_perplexity_cookies()
    
    if cookies:
        logger.info(f"성공적으로 {len(cookies)} 개의 Perplexity 쿠키를 찾았습니다.")
        try:
            global_client = await Client(cookies=cookies)
            logger.info("Perplexity 클라이언트 초기화 성공!")
            return True
        except Exception as e:
            logger.error(f"Perplexity 클라이언트 초기화 실패: {e}")
            return False
    else:
        logger.warning("Perplexity 쿠키를 찾을 수 없습니다. 빈 쿠키로 클라이언트 초기화를 시도합니다.")
        try:
            global_client = await Client(cookies={})
            logger.info("빈 쿠키로 Perplexity 클라이언트 초기화 성공!")
            return True
        except Exception as e:
            logger.error(f"빈 쿠키로 Perplexity 클라이언트 초기화 실패: {e}")
            return False

# lifespan 컨텍스트 매니저 구현
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("서버 시작: 클라이언트 초기화 중...")
    await initialize_client()
    yield
    logger.info("서버 종료")

app = FastAPI(lifespan=lifespan)

def format_query(query: str, output_format: str = "markdown") -> str:
    """쿼리에 출력 형식 요청을 추가하는 함수"""
    if output_format == "markdown":
        instruction = "\n\n답변을 마크다운(Markdown) 형식으로 작성해주세요. 제목은 ##, 중요한 내용은 **굵게**, 목록은 - 또는 1. 를 사용해주세요. 답변을 완전하게 작성해주세요. 답변이 완료되면 반드시 '|end_task|'를 마지막에 붙여주세요."
    else:
        instruction = "\n\n답변을 일반 텍스트 형식으로 간단명료하게 작성해주세요. 특수 문자나 마크다운 문법 없이 작성해주세요. 답변이 완료되면 반드시 '|end_task|'를 마지막에 붙여주세요."
    
    return query + instruction

async def get_complete_response(client, query, max_retries=3):
    """완전한 응답을 받을 때까지 재시도하는 함수"""
    for attempt in range(max_retries):
        try:
            logger.info(f"응답 시도 {attempt + 1}/{max_retries}")
            
            response = await client.search(
                query=query,
                mode='auto',
                stream=False,
                language='ko-KR'
            )
            
            if response:
                # 응답에서 답변 텍스트 추출
                clean_answer = extract_clean_answer(response)
                
                # 완전한 응답인지 확인
                if (clean_answer and 
                    clean_answer != "답변을 찾을 수 없습니다." and
                    is_complete_response(clean_answer)):
                    logger.info(f"완전한 응답 받음 (길이: {len(clean_answer)})")
                    return response
                else:
                    logger.warning(f"불완전한 응답 감지, 재시도 중...")
                    if attempt < max_retries - 1:
                        await asyncio.sleep(3)
            else:
                logger.warning("응답이 None, 재시도 중...")
                if attempt < max_retries - 1:
                    await asyncio.sleep(3)
                    
        except Exception as e:
            logger.error(f"응답 시도 {attempt + 1} 실패: {e}")
            if attempt < max_retries - 1:
                await asyncio.sleep(3)
            else:
                raise e
    
    logger.warning("모든 재시도 실패, 마지막 응답 반환")
    return response if 'response' in locals() else None

class ChatRequest(BaseModel):
    query: str = Field(..., description="검색할 쿼리")
    output_format: Optional[str] = Field("markdown", description="출력 형식: 'markdown' 또는 'plain'")
    cookies: Optional[Dict[str, str]] = Field(None, description="사용할 쿠키 (선택사항)")

@app.post("/chat")
async def chat_endpoint(request: ChatRequest):
    global global_client
    
    try:
        logger.info(f"chat 요청: 쿼리='{request.query}', 형식='{request.output_format}'")
        
        # 쿼리 포맷팅
        formatted_query = format_query(request.query, request.output_format)
        
        # 클라이언트 설정
        if request.cookies:
            logger.info("제공된 쿠키로 임시 클라이언트 생성")
            temp_client = await Client(cookies=request.cookies)
            response = await get_complete_response(temp_client, formatted_query)
        else:
            if global_client is None:
                success = await initialize_client()
                if not success:
                    raise HTTPException(status_code=500, detail="클라이언트 초기화 실패")
            
            response = await get_complete_response(global_client, formatted_query)
        
        if response:
            clean_answer = extract_clean_answer(response)
            
            # |end_task| 마커 제거
            if "|end_task|" in clean_answer:
                clean_answer = clean_answer.replace("|end_task|", "").strip()
            
            if request.output_format == "plain":
                # 플레인 텍스트로 변환
                plain_answer = convert_to_plain_text(clean_answer)
                return {
                    "answer": plain_answer,
                    "format": "plain"
                }
            else:
                # 마크다운 형식 그대로 반환
                return {
                    "answer": clean_answer,
                    "format": "markdown"
                }
        else:
            return {"error": "응답을 받을 수 없습니다"}
            
    except Exception as e:
        logger.error(f"오류: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
