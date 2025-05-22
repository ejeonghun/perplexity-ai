# Perplexity API 테스트 스크립트 (PowerShell)

# 기본 URL 설정 (로컬 또는 원격 서버 URL로 변경 가능)
$API_URL = "http://localhost:8000"

Write-Host "Perplexity API 테스트 스크립트" -ForegroundColor Yellow
Write-Host "--------------------------------"

# API가 실행 중인지 확인
Write-Host "[1] API 서버 연결 확인" -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri $API_URL -Method Head -UseBasicParsing -ErrorAction SilentlyContinue
    Write-Host "API 서버가 실행 중입니다." -ForegroundColor Green
} catch {
    Write-Host "API 서버에 연결할 수 없습니다. 서버가 실행 중인지 확인하세요." -ForegroundColor Red
    exit
}

Write-Host ""
Write-Host "[2] 클라이언트 갱신 테스트 (/refresh-client)" -ForegroundColor Yellow
Write-Host "클라이언트 갱신 중..."
$refreshResponse = Invoke-RestMethod -Uri "$API_URL/refresh-client" -Method Get -ContentType "application/json"
$refreshResponse | ConvertTo-Json
Write-Host ""

# /test-chat 엔드포인트 테스트 (쿠키 없이)
Write-Host "[3] 테스트 채팅 API 테스트 (/test-chat)" -ForegroundColor Yellow
Write-Host "쿼리: '안녕하세요, 간단한 질문입니다.'"
$body = @{
    query = "안녕하세요, 간단한 질문입니다."
} | ConvertTo-Json

$testChatResponse = Invoke-RestMethod -Uri "$API_URL/test-chat" -Method Post -Body $body -ContentType "application/json"
$testChatResponse | ConvertTo-Json -Depth 5
Write-Host ""

# /chat 엔드포인트 테스트 (쿠키 없이)
Write-Host "[4] 채팅 API 테스트 - 쿠키 없음 (/chat)" -ForegroundColor Yellow
Write-Host "쿼리: '파이썬이란 무엇인가요?'"
$body = @{
    query = "파이썬이란 무엇인가요?"
} | ConvertTo-Json

$chatResponse = Invoke-RestMethod -Uri "$API_URL/chat" -Method Post -Body $body -ContentType "application/json"
$chatResponse | ConvertTo-Json -Depth 5
Write-Host ""

# /chat 엔드포인트 테스트 (예시 쿠키 포함)
Write-Host "[5] 채팅 API 테스트 - 쿠키 포함 (/chat)" -ForegroundColor Yellow
Write-Host "쿼리: '인공지능의 역사는?'"
Write-Host "쿠키 예시를 포함한 요청입니다 (실제 쿠키 값으로 변경 필요)"
$body = @{
    query = "인공지능의 역사는?"
    cookies = @{
        "perplexity.ai.sid" = "여기에_실제_쿠키_값을_입력하세요"
        "token" = "여기에_실제_토큰_값을_입력하세요"
    }
} | ConvertTo-Json

try {
    $chatWithCookiesResponse = Invoke-RestMethod -Uri "$API_URL/chat" -Method Post -Body $body -ContentType "application/json"
    $chatWithCookiesResponse | ConvertTo-Json -Depth 5
} catch {
    Write-Host "에러 발생: $_" -ForegroundColor Red
    Write-Host "쿠키 값을 실제 유효한 값으로 변경해야 합니다." -ForegroundColor Yellow
}

Write-Host ""
Write-Host "모든 테스트가 완료되었습니다." -ForegroundColor Green