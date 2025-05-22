#!/bin/bash
# Perplexity API 테스트 스크립트

# 기본 URL 설정 (로컬 또는 원격 서버 URL로 변경 가능)
API_URL="http://localhost:8000"

# 색상 설정
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Perplexity API 테스트 스크립트${NC}"
echo "--------------------------------"

# API가 실행 중인지 확인
echo -e "${YELLOW}[1] API 서버 연결 확인${NC}"
if curl -s --head "$API_URL" | grep "200\|404" > /dev/null; then
  echo -e "${GREEN}API 서버가 실행 중입니다.${NC}"
else
  echo -e "${RED}API 서버에 연결할 수 없습니다. 서버가 실행 중인지 확인하세요.${NC}"
  exit 1
fi

echo ""
echo -e "${YELLOW}[2] 클라이언트 갱신 테스트 (/refresh-client)${NC}"
echo "클라이언트 갱신 중..."
curl -s -X GET "$API_URL/refresh-client" | jq .
echo ""

# /test-chat 엔드포인트 테스트 (쿠키 없이)
echo -e "${YELLOW}[3] 테스트 채팅 API 테스트 (/test-chat)${NC}"
echo "쿼리: '안녕하세요, 간단한 질문입니다.'"
curl -s -X POST "$API_URL/test-chat" \
  -H "Content-Type: application/json" \
  -d '{"query":"안녕하세요, 간단한 질문입니다."}' | jq .
echo ""

# /chat 엔드포인트 테스트 (쿠키 없이)
echo -e "${YELLOW}[4] 채팅 API 테스트 - 쿠키 없음 (/chat)${NC}"
echo "쿼리: '파이썬이란 무엇인가요?'"
curl -s -X POST "$API_URL/chat" \
  -H "Content-Type: application/json" \
  -d '{"query":"파이썬이란 무엇인가요?"}' | jq .
echo ""

# /chat 엔드포인트 테스트 (예시 쿠키 포함)
echo -e "${YELLOW}[5] 채팅 API 테스트 - 쿠키 포함 (/chat)${NC}"
echo "쿼리: '인공지능의 역사는?'"
echo "쿠키 예시를 포함한 요청입니다 (실제 쿠키 값으로 변경 필요)"
curl -s -X POST "$API_URL/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "query":"인공지능의 역사는?",
    "cookies":{
      "perplexity.ai.sid": "여기에_실제_쿠키_값을_입력하세요",
      "token": "여기에_실제_토큰_값을_입력하세요"
    }
  }' | jq .
echo ""

echo -e "${GREEN}모든 테스트가 완료되었습니다.${NC}"