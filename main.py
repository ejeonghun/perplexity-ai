from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import Dict, Optional
from perplexity_async.client import Client
import asyncio
import logging
from contextlib import asynccontextmanager
from cookie import get_perplexity_cookies

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 전역 Client 변수
global_client = None
last_cookie_check = None

# 쿠키 유효성 확인 및 클라이언트 초기화 함수
async def initialize_client():
    global global_client
    
    # 브라우저에서 쿠키 가져오기
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
    # 서버 시작 시 실행되는 코드
    logger.info("서버 시작: 클라이언트 초기화 중...")
    await initialize_client()
    
    # 다음 코드는 라우트 처리를 위해 FastAPI에 제어권을 넘김
    yield
    
    # 서버 종료 시 실행되는 코드
    logger.info("서버 종료: 필요한 정리 작업 수행 중...")
    # 여기에 필요한 정리 코드 추가

# lifespan 컨텍스트 매니저 등록
app = FastAPI(lifespan=lifespan)

class ChatRequest(BaseModel):
    query: str = Field(..., description="The search query for Perplexity.")
    cookies: Optional[Dict[str, str]] = Field(None, description="Optional cookies to be used for the Perplexity client session.")

class TestChatRequest(BaseModel):
    query: str = Field(..., description="The search query for Perplexity.")

@app.post("/chat")
async def chat_endpoint(request: ChatRequest):
    global global_client
    
    try:
        logger.info(f"chat 요청 받음: 쿼리='${request.query}'")
        
        # 요청에 쿠키가 제공된 경우 해당 쿠키로 임시 클라이언트 사용
        if request.cookies:
            logger.info("요청에서 제공된 쿠키로 임시 클라이언트 생성")
            temp_client = await Client(cookies=request.cookies)
            logger.info("검색 시작...")
            try:
                # 타임아웃 30초 설정
                response = await asyncio.wait_for(
                    temp_client.search(query=request.query),
                    timeout=30.0
                )
                logger.info("검색 완료, 응답 반환")
            except asyncio.TimeoutError:
                logger.error("검색 타임아웃 발생")
                raise HTTPException(status_code=504, detail="Perplexity API 타임아웃")
        # 그렇지 않으면 전역 클라이언트 사용
        else:
            # 전역 클라이언트가 없으면 초기화
            if global_client is None:
                logger.info("전역 클라이언트 초기화 필요")
                success = await initialize_client()
                if not success:
                    logger.error("클라이언트 초기화 실패")
                    raise HTTPException(status_code=500, detail="Perplexity 클라이언트 초기화에 실패했습니다.")
            
            logger.info("전역 Perplexity 클라이언트로 검색 수행")
            try:
                # 타임아웃 30초 설정
                response = await asyncio.wait_for(
                    global_client.search(query=request.query),
                    timeout=30.0
                )
                logger.info("검색 완료, 응답 반환")
            except asyncio.TimeoutError:
                logger.error("검색 타임아웃 발생")
                raise HTTPException(status_code=504, detail="Perplexity API 타임아웃")
        
        logger.info(f"응답 타입: {type(response)}")
        if response:
            logger.info("응답 데이터가 존재함")
        else:
            logger.warning("응답 데이터가 없음 (None)")
        
        return response
    except Exception as e:
        logger.error(f"Perplexity 검색 중 오류: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/test-chat")
async def test_chat_endpoint(request: TestChatRequest):
    global global_client
    
    try:
        # 전역 클라이언트가 없으면 초기화
        if global_client is None:
            success = await initialize_client()
            if not success:
                raise HTTPException(status_code=500, detail="Perplexity 클라이언트 초기화에 실패했습니다.")
        
        logger.info("전역 Perplexity 클라이언트로 테스트 검색 수행")
        response = await global_client.search(query=request.query, mode='auto')
        return response
    except Exception as e:
        logger.error(f"Perplexity 테스트 검색 중 오류: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/refresh-client")
async def refresh_client():
    """쿠키를 다시 가져와서 클라이언트를 갱신합니다."""
    success = await initialize_client()
    if success:
        return {"status": "success", "message": "클라이언트가 성공적으로 갱신되었습니다."}
    else:
        raise HTTPException(status_code=500, detail="클라이언트 갱신에 실패했습니다.")
