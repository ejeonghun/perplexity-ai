from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import Dict, Optional, List
import httpx
import re
from urllib.parse import urlparse
import logging

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="AI 기능 확장 서비스", description="YouTube 요약, 블로그 정리 등 다양한 AI 기능")

# Perplexity API 호출 함수
async def call_perplexity_api(query: str, output_format: str = "markdown") -> dict:
    """main.py의 /chat 엔드포인트를 호출하는 함수"""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8000/chat",
            json={
                "query": query,
                "output_format": output_format
            },
            timeout=120.0
        )
        response.raise_for_status()
        return response.json()

# 1. YouTube 요약 기능
class YouTubeRequest(BaseModel):
    url: str = Field(..., description="YouTube 비디오 URL")
    summary_type: Optional[str] = Field("detailed", description="요약 타입: 'brief', 'detailed', 'key_points'")
    language: Optional[str] = Field("korean", description="요약 언어")

@app.post("/youtube/summary")
async def youtube_summary(request: YouTubeRequest):
    """YouTube 비디오 요약 기능"""
    try:
        # YouTube URL 유효성 검사
        if not ("youtube.com" in request.url or "youtu.be" in request.url):
            raise HTTPException(status_code=400, detail="유효한 YouTube URL이 아닙니다.")
        
        # 요약 타입별 프롬프트 설정
        if request.summary_type == "brief":
            prompt = f"""
            다음 YouTube 비디오를 분석하고 간단한 요약을 제공해주세요:
            {request.url}
            
            **요청사항:**
            - 3-5문장으로 핵심 내용만 요약
            - 주요 포인트 1-3개만 언급
            - {request.language}로 작성
            
            **형식:**
            ## 📺 비디오 요약
            [간단한 요약 내용]
            
            **핵심 포인트:**
            - 포인트 1
            - 포인트 2
            """
        elif request.summary_type == "key_points":
            prompt = f"""
            다음 YouTube 비디오의 핵심 포인트들을 정리해주세요:
            {request.url}
            
            **요청사항:**
            - 주요 내용을 5-10개의 핵심 포인트로 정리
            - 각 포인트는 구체적이고 실용적으로
            - {request.language}로 작성
            
            **형식:**
            ## 🎯 핵심 포인트 정리
            
            ### 📋 주요 내용
            1. 포인트 1
            2. 포인트 2
            ...
            
            ### 💡 실용적 조언 (있다면)
            - 조언 1
            - 조언 2
            """
        else:  # detailed
            prompt = f"""
            다음 YouTube 비디오에 대한 상세한 요약을 작성해주세요:
            {request.url}
            
            **요청사항:**
            - 비디오의 전체적인 구조와 흐름 파악
            - 주요 섹션별로 내용 정리
            - 중요한 인사이트나 정보 강조
            - {request.language}로 작성
            
            **형식:**
            ## 📺 [비디오 제목]
            
            ### 📊 비디오 정보
            - 채널명: [채널명]
            - 주제: [주제]
            - 길이: [길이 정보]
            
            ### 📝 상세 요약
            #### 1. 도입부
            [도입부 내용]
            
            #### 2. 주요 내용
            [주요 내용들]
            
            #### 3. 결론
            [결론 부분]
            
            ### 🎯 핵심 takeaway
            - 중요 포인트 1
            - 중요 포인트 2
            """
        
        # Perplexity API 호출
        result = await call_perplexity_api(prompt)
        
        return {
            "url": request.url,
            "summary_type": request.summary_type,
            "language": request.language,
            "summary": result.get("answer", "요약을 생성할 수 없습니다.")
        }
        
    except Exception as e:
        logger.error(f"YouTube 요약 오류: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# 2. 블로그 정리 기능
class BlogRequest(BaseModel):
    keyword: str = Field(..., description="블로그 주제 키워드")
    target_audience: Optional[str] = Field("일반인", description="대상 독자층")
    post_length: Optional[str] = Field("medium", description="포스트 길이: 'short', 'medium', 'long'")
    include_seo: Optional[bool] = Field(True, description="SEO 최적화 포함 여부")

@app.post("/blog/create")
async def create_blog_post(request: BlogRequest):
    """키워드 기반 블로그 포스트 생성"""
    try:
        # 포스트 길이별 설정
        length_settings = {
            "short": "1000-1500자, 간결하고 핵심적인",
            "medium": "2000-3000자, 상세하면서도 읽기 쉬운",
            "long": "3000-5000자, 매우 상세하고 전문적인"
        }
        
        length_desc = length_settings.get(request.post_length, length_settings["medium"])
        
        prompt = f"""
        "{request.keyword}"에 대한 블로그 포스트를 작성해주세요.
        
        **요청사항:**
        - 웹에서 최신 정보를 검색하여 정확하고 신뢰할 수 있는 내용으로 작성
        - 대상 독자: {request.target_audience}
        - 글 길이: {length_desc}
        - 읽기 쉽고 매력적인 블로그 형태로 작성
        
        **포함할 내용:**
        1. 주제에 대한 기본 개념 설명
        2. 최신 트렌드나 변화사항
        3. 실용적인 팁이나 조언
        4. 구체적인 예시나 사례
        5. 독자에게 도움이 되는 실행 가능한 정보
        
        **블로그 포스트 형식:**
        # {request.keyword}: [매력적인 제목]
        
        ## 🔍 들어가며
        [흥미로운 도입부 - 독자의 관심을 끄는 내용]
        
        ## 📚 {request.keyword}란 무엇인가?
        [기본 개념과 정의]
        
        ## 🔥 최신 트렌드와 변화
        [현재 상황과 최신 동향]
        
        ## 💡 실용적인 팁과 조언
        [독자가 바로 활용할 수 있는 정보]
        
        ## 📋 구체적인 예시/사례
        [실제 사례나 예시]
        
        ## 🎯 핵심 요약
        [주요 포인트 정리]
        
        ## 🤔 마무리
        [결론과 독자에게 전하는 메시지]
        """
        
        if request.include_seo:
            prompt += f"""
            
            **SEO 최적화 요소도 함께 제공해주세요:**
            - 메타 설명 (150자 이내)
            - 추천 해시태그 5-10개
            - 관련 키워드 5-8개
            """
        
        # Perplexity API 호출
        result = await call_perplexity_api(prompt)
        
        response_data = {
            "keyword": request.keyword,
            "target_audience": request.target_audience,
            "post_length": request.post_length,
            "blog_post": result.get("answer", "블로그 포스트를 생성할 수 없습니다.")
        }
        
        return response_data
        
    except Exception as e:
        logger.error(f"블로그 생성 오류: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# 3. 뉴스 요약 및 분석 기능
class NewsRequest(BaseModel):
    topic: str = Field(..., description="뉴스 주제")
    date_range: Optional[str] = Field("recent", description="기간: 'today', 'week', 'month', 'recent'")
    analysis_type: Optional[str] = Field("summary", description="분석 타입: 'summary', 'trend', 'impact'")

@app.post("/news/analyze")
async def analyze_news(request: NewsRequest):
    """뉴스 분석 및 요약"""
    try:
        date_mapping = {
            "today": "오늘",
            "week": "최근 1주일",
            "month": "최근 1개월",
            "recent": "최근"
        }
        
        date_desc = date_mapping.get(request.date_range, "최근")
        
        if request.analysis_type == "trend":
            prompt = f"""
            "{request.topic}"에 대한 {date_desc} 뉴스를 검색하고 트렌드 분석을 해주세요.
            
            **분석 형식:**
            ## 📰 {request.topic} 뉴스 트렌드 분석
            
            ### 📊 주요 동향
            [현재 주요 흐름과 변화]
            
            ### 📈 트렌드 포인트
            1. 증가하는 이슈: [내용]
            2. 감소하는 이슈: [내용]
            3. 새로 등장한 이슈: [내용]
            
            ### 🔮 향후 전망
            [앞으로의 예상 흐름]
            
            ### 📌 주목할 키워드
            - 키워드 1
            - 키워드 2
            """
        elif request.analysis_type == "impact":
            prompt = f"""
            "{request.topic}"에 대한 {date_desc} 뉴스를 검색하고 영향 분석을 해주세요.
            
            **분석 형식:**
            ## 🎯 {request.topic} 영향 분석
            
            ### 💼 경제적 영향
            [경제/비즈니스에 미치는 영향]
            
            ### 👥 사회적 영향
            [사회/문화에 미치는 영향]
            
            ### 🏛️ 정치적 영향
            [정치/정책에 미치는 영향]
            
            ### 🌍 글로벌 영향
            [국제적 파급효과]
            
            ### ⚠️ 리스크와 기회
            **리스크:**
            - 리스크 1
            - 리스크 2
            
            **기회:**
            - 기회 1
            - 기회 2
            """
        else:  # summary
            prompt = f"""
            "{request.topic}"에 대한 {date_desc} 주요 뉴스를 검색하고 종합 요약해주세요.
            
            **요약 형식:**
            ## 📰 {request.topic} 뉴스 종합
            
            ### 🔥 주요 헤드라인
            [가장 중요한 뉴스 3-5개]
            
            ### 📝 상세 내용
            #### 1. [뉴스 제목 1]
            [내용 요약]
            
            #### 2. [뉴스 제목 2]
            [내용 요약]
            
            ### 💭 전문가 의견
            [관련 전문가나 기관의 의견]
            
            ### 🎯 핵심 포인트
            - 포인트 1
            - 포인트 2
            """
        
        result = await call_perplexity_api(prompt)
        
        return {
            "topic": request.topic,
            "date_range": request.date_range,
            "analysis_type": request.analysis_type,
            "analysis": result.get("answer", "뉴스 분석을 생성할 수 없습니다.")
        }
        
    except Exception as e:
        logger.error(f"뉴스 분석 오류: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# 4. 학습 자료 생성 기능
class StudyRequest(BaseModel):
    subject: str = Field(..., description="학습 주제")
    level: Optional[str] = Field("intermediate", description="난이도: 'beginner', 'intermediate', 'advanced'")
    format_type: Optional[str] = Field("guide", description="형식: 'guide', 'quiz', 'summary', 'flashcard'")

@app.post("/study/create")
async def create_study_material(request: StudyRequest):
    """학습 자료 생성"""
    try:
        level_mapping = {
            "beginner": "초급자용 (기초부터 차근차근)",
            "intermediate": "중급자용 (기본 지식 보유자)",
            "advanced": "고급자용 (심화 내용 중심)"
        }
        
        level_desc = level_mapping.get(request.level, level_mapping["intermediate"])
        
        if request.format_type == "quiz":
            prompt = f"""
            "{request.subject}"에 대한 {level_desc} 퀴즈를 만들어주세요.
            
            **퀴즈 형식:**
            ## 📚 {request.subject} 학습 퀴즈
            
            ### 🎯 객관식 문제 (5문제)
            **문제 1:** [문제]
            1) 선택지 1
            2) 선택지 2
            3) 선택지 3
            4) 선택지 4
            
            ### ✍️ 주관식 문제 (3문제)
            **문제 1:** [문제]
            
            ### 💡 정답 및 해설
            **객관식 정답:**
            1. 정답: X번 - [해설]
            
            **주관식 해설:**
            1. [상세한 답안 및 해설]
            """
        elif request.format_type == "summary":
            prompt = f"""
            "{request.subject}"에 대한 {level_desc} 학습 요약 자료를 만들어주세요.
            
            **요약 형식:**
            ## 📖 {request.subject} 핵심 요약
            
            ### 🎯 학습 목표
            [이 자료로 배울 수 있는 것들]
            
            ### 📚 핵심 개념
            #### 1. 기본 개념
            [기초 이론과 정의]
            
            #### 2. 주요 원리
            [핵심 원리들]
            
            #### 3. 실제 적용
            [실무/실생활 적용 사례]
            
            ### 🔍 심화 내용
            [더 깊이 알아야 할 내용]
            
            ### 📝 체크포인트
            - [ ] 체크할 항목 1
            - [ ] 체크할 항목 2
            
            ### 🎓 추가 학습 자료
            [더 공부할 수 있는 방향성]
            """
        elif request.format_type == "flashcard":
            prompt = f"""
            "{request.subject}"에 대한 {level_desc} 플래시카드를 만들어주세요.
            
            **플래시카드 형식:**
            ## 🗂️ {request.subject} 플래시카드
            
            ### 카드 1
            **앞면:** [질문이나 개념]
            **뒷면:** [답안이나 설명]
            
            ### 카드 2
            **앞면:** [질문이나 개념]
            **뒷면:** [답안이나 설명]
            
            [15-20개의 카드 생성]
            
            ### 📚 활용 팁
            [플래시카드 효과적인 사용법]
            """
        else:  # guide
            prompt = f"""
            "{request.subject}"에 대한 {level_desc} 학습 가이드를 만들어주세요.
            
            **가이드 형식:**
            ## 📘 {request.subject} 완벽 학습 가이드
            
            ### 🎯 시작하기 전에
            [학습 전 준비사항과 마음가짐]
            
            ### 📅 학습 로드맵
            #### 1단계: 기초 다지기 (예상 소요: X시간)
            [기초 내용과 학습 방법]
            
            #### 2단계: 핵심 이해 (예상 소요: X시간)
            [핵심 내용과 실습]
            
            #### 3단계: 실전 적용 (예상 소요: X시간)
            [응용과 프로젝트]
            
            ### 📚 추천 학습 자료
            [책, 강의, 웹사이트 등]
            
            ### ⚠️ 주의사항과 팁
            [학습 시 주의할 점과 효과적인 방법]
            
            ### 🎯 학습 점검 체크리스트
            - [ ] 항목 1
            - [ ] 항목 2
            """
        
        result = await call_perplexity_api(prompt)
        
        return {
            "subject": request.subject,
            "level": request.level,
            "format_type": request.format_type,
            "study_material": result.get("answer", "학습 자료를 생성할 수 없습니다.")
        }
        
    except Exception as e:
        logger.error(f"학습 자료 생성 오류: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# 5. 웹사이트 분석 기능
class WebsiteRequest(BaseModel):
    url: str = Field(..., description="분석할 웹사이트 URL")
    analysis_type: Optional[str] = Field("content", description="분석 타입: 'content', 'seo', 'competitor', 'user_experience'")

@app.post("/website/analyze")
async def analyze_website(request: WebsiteRequest):
    """웹사이트 분석"""
    try:
        # URL 유효성 검사
        parsed_url = urlparse(request.url)
        if not parsed_url.scheme or not parsed_url.netloc:
            raise HTTPException(status_code=400, detail="유효한 URL이 아닙니다.")
        
        if request.analysis_type == "seo":
            prompt = f"""
            다음 웹사이트의 SEO 분석을 해주세요: {request.url}
            
            **SEO 분석 형식:**
            ## 🔍 SEO 분석 리포트
            
            ### 📊 기본 정보
            - 도메인: [도메인 정보]
            - 주요 키워드: [예상 타겟 키워드]
            
            ### 🎯 SEO 강점
            [잘 되어 있는 SEO 요소들]
            
            ### ⚠️ 개선 필요 사항
            [개선이 필요한 SEO 요소들]
            
            ### 📈 추천 개선사항
            1. 메타 태그 최적화
            2. 콘텐츠 키워드 밀도
            3. 페이지 속도 개선
            4. 모바일 최적화
            5. 백링크 구축
            
            ### 🏆 경쟁사 비교
            [유사한 사이트와의 비교 분석]
            """
        elif request.analysis_type == "competitor":
            prompt = f"""
            다음 웹사이트의 경쟁사 분석을 해주세요: {request.url}
            
            **경쟁사 분석 형식:**
            ## 🥊 경쟁사 분석 리포트
            
            ### 🎯 주요 경쟁사
            [직접 경쟁사 3-5개 업체]
            
            ### 📊 비교 분석
            #### 장점
            [이 사이트만의 강점]
            
            #### 단점
            [경쟁사 대비 약점]
            
            ### 💡 벤치마킹 포인트
            [경쟁사에서 배워야 할 점들]
            
            ### 🚀 차별화 전략
            [경쟁에서 이기기 위한 전략]
            """
        elif request.analysis_type == "user_experience":
            prompt = f"""
            다음 웹사이트의 사용자 경험(UX) 분석을 해주세요: {request.url}
            
            **UX 분석 형식:**
            ## 👥 사용자 경험 분석
            
            ### 🎨 디자인 및 레이아웃
            [시각적 디자인과 레이아웃 평가]
            
            ### 🧭 네비게이션
            [메뉴 구조와 사용성]
            
            ### 📱 반응형 디자인
            [모바일/태블릿 호환성]
            
            ### ⚡ 성능
            [로딩 속도와 최적화]
            
            ### 🔍 검색 및 필터
            [사이트 내 검색 기능]
            
            ### 💬 사용자 피드백
            [리뷰, 댓글 등 피드백 시스템]
            
            ### 📈 개선 권장사항
            1. 우선순위 높은 개선사항
            2. 중간 우선순위 개선사항
            3. 장기적 개선사항
            """
        else:  # content
            prompt = f"""
            다음 웹사이트의 콘텐츠 분석을 해주세요: {request.url}
            
            **콘텐츠 분석 형식:**
            ## 📄 콘텐츠 분석 리포트
            
            ### 🎯 사이트 개요
            [사이트의 목적과 타겟 오디언스]
            
            ### 📚 주요 콘텐츠
            [메인 콘텐츠와 카테고리]
            
            ### ✍️ 콘텐츠 품질
            #### 강점
            [잘 작성된 콘텐츠의 특징]
            
            #### 개선점
            [콘텐츠 개선이 필요한 부분]
            
            ### 📊 콘텐츠 전략
            [콘텐츠 마케팅 관점에서의 분석]
            
            ### 💡 콘텐츠 추천사항
            1. 추가하면 좋을 콘텐츠 유형
            2. 개선이 필요한 기존 콘텐츠
            3. 콘텐츠 최적화 방안
            """
        
        result = await call_perplexity_api(prompt)
        
        return {
            "url": request.url,
            "analysis_type": request.analysis_type,
            "analysis": result.get("answer", "웹사이트 분석을 생성할 수 없습니다.")
        }
        
    except Exception as e:
        logger.error(f"웹사이트 분석 오류: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# 6. 창작 도우미 기능
class CreativeRequest(BaseModel):
    content_type: str = Field(..., description="콘텐츠 타입: 'story', 'poem', 'script', 'song', 'speech'")
    theme: str = Field(..., description="주제나 테마")
    tone: Optional[str] = Field("neutral", description="톤: 'formal', 'casual', 'humorous', 'emotional', 'professional'")
    length: Optional[str] = Field("medium", description="길이: 'short', 'medium', 'long'")

@app.post("/creative/generate")
async def generate_creative_content(request: CreativeRequest):
    """창작 콘텐츠 생성"""
    try:
        tone_mapping = {
            "formal": "격식있고 정중한",
            "casual": "편안하고 친근한",
            "humorous": "유머러스하고 재미있는",
            "emotional": "감동적이고 따뜻한",
            "professional": "전문적이고 신뢰할 수 있는"
        }
        
        tone_desc = tone_mapping.get(request.tone, "자연스러운")
        
        if request.content_type == "story":
            prompt = f"""
            "{request.theme}"를 주제로 한 {tone_desc} 톤의 단편소설을 써주세요.
            
            **스토리 요구사항:**
            - 길이: {request.length} 형태
            - 톤: {tone_desc}
            - 흥미진진한 플롯과 캐릭터
            - 명확한 시작, 중간, 끝
            
            **형식:**
            ## 📖 [제목]
            
            ### 등장인물
            [주요 캐릭터 소개]
            
            ### 본문
            [스토리 내용]
            
            ### 에필로그
            [마무리나 여운]
            """
        elif request.content_type == "poem":
            prompt = f"""
            "{request.theme}"를 주제로 한 {tone_desc} 시를 써주세요.
            
            **시 요구사항:**
            - 감정이 잘 표현된 시어 사용
            - 운율과 리듬감 고려
            - 톤: {tone_desc}
            
            **형식:**
            ## 🌟 [시 제목]
            
            [시 본문]
            
            ### 시상 노트
            [시의 의미나 영감에 대한 설명]
            """
        elif request.content_type == "script":
            prompt = f"""
            "{request.theme}"를 주제로 한 {tone_desc} 대본을 써주세요.
            
            **대본 형식:**
            ## 🎬 [제목]
            
            ### 등장인물
            - [캐릭터 1]: [설명]
            - [캐릭터 2]: [설명]
            
            ### 장면 1
            [장소와 상황 설명]
            
            **캐릭터 A**: 대사 내용
            **캐릭터 B**: 대사 내용
            
            (행동 지시사항)
            """
        elif request.content_type == "song":
            prompt = f"""
            "{request.theme}"를 주제로 한 {tone_desc} 가사를 써주세요.
            
            **가사 형식:**
            ## 🎵 [곡 제목]
            
            ### 1절
            [가사]
            
            ### 후렴구
            [가사]
            
            ### 2절
            [가사]
            
            ### 후렴구
            [가사]
            
            ### 브릿지
            [가사]
            
            ### 마지막 후렴구
            [가사]
            
            ### 🎼 곡 정보
            - 장르: [추천 장르]
            - 분위기: [곡의 분위기]
            - 템포: [빠르기 추천]
            """
        else:  # speech
            prompt = f"""
            "{request.theme}"를 주제로 한 {tone_desc} 연설문을 써주세요.
            
            **연설문 형식:**
            ## 🎤 [연설 제목]
            
            ### 도입부
            [청중의 관심을 끄는 시작]
            
            ### 본론
            #### 1. 첫 번째 포인트
            [주요 내용]
            
            #### 2. 두 번째 포인트
            [주요 내용]
            
            #### 3. 세 번째 포인트
            [주요 내용]
            
            ### 결론
            [강력한 마무리와 호출]
            
            ### 📝 연설 팁
            [효과적인 전달을 위한 조언]
            """
        
        result = await call_perplexity_api(prompt)
        
        return {
            "content_type": request.content_type,
            "theme": request.theme,
            "tone": request.tone,
            "length": request.length,
            "creative_content": result.get("answer", "창작 콘텐츠를 생성할 수 없습니다.")
        }
        
    except Exception as e:
        logger.error(f"창작 콘텐츠 생성 오류: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# 헬스체크 엔드포인트
@app.get("/health")
async def health_check():
    return {"status": "healthy", "message": "AI 기능 확장 서비스가 정상 작동 중입니다."}

@app.get("/")
async def root():
    return {
        "title": "AI 기능 확장 서비스",
        "features": [
            "YouTube 요약 (/youtube/summary)",
            "블로그 포스트 생성 (/blog/create)",
            "뉴스 분석 (/news/analyze)",
            "학습 자료 생성 (/study/create)",
            "웹사이트 분석 (/website/analyze)",
            "창작 도우미 (/creative/generate)"
        ],
        "docs": "/docs"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)