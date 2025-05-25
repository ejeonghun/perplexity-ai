import json
import re
import html
from typing import Dict, Any, Union

def clean_escaped_text(text: str) -> str:
    """이스케이프된 텍스트를 정리하는 함수"""
    if not text:
        return text
    
    # JSON 문자열에서 이스케이프된 문자들을 정리
    text = text.replace('\\"', '"')  # 따옴표 이스케이프 제거
    text = text.replace('\\n', '\n')  # 개행 문자 정리
    text = text.replace('\\t', '\t')  # 탭 문자 정리
    text = text.replace('\\\\', '\\')  # 이중 백슬래시 정리
    
    # 한글 및 기타 문자의 백슬래시 이스케이프 제거 (예: \주\식 -> 주식)
    text = re.sub(r'\\(.)', r'\1', text)
    
    # HTML 엔티티 디코딩
    text = html.unescape(text)
    
    # 연속된 공백 정리
    text = re.sub(r'\s+', ' ', text)
    
    # 불필요한 줄바꿈 정리
    text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)  # 3개 이상의 연속 줄바꿈을 2개로
    
    return text.strip()

def format_markdown_links(text: str) -> str:
    """Perplexity 특수 링크를 일반 마크다운으로 변환"""
    # pplx://action/followup 링크를 볼드 텍스트로 변환
    text = re.sub(r'\[([^\]]+)\]\(pplx://action/followup\)', r'**\1**', text)
    
    # 기타 특수 링크도 처리
    text = re.sub(r'\[([^\]]+)\]\(pplx://[^)]+\)', r'**\1**', text)
    
    return text

def clean_web_results(web_results: list) -> list:
    """웹 검색 결과의 텍스트들을 정리"""
    if not web_results:
        return web_results
    
    cleaned_results = []
    for result in web_results:
        if isinstance(result, dict):
            cleaned_result = result.copy()
            
            # name 필드 정리
            if 'name' in cleaned_result:
                cleaned_result['name'] = clean_escaped_text(cleaned_result['name'])
            
            # snippet 필드 정리
            if 'snippet' in cleaned_result:
                cleaned_result['snippet'] = clean_escaped_text(cleaned_result['snippet'])
            
            # description 필드 정리 (meta_data 내부)
            if 'meta_data' in cleaned_result and isinstance(cleaned_result['meta_data'], dict):
                if 'description' in cleaned_result['meta_data']:
                    cleaned_result['meta_data']['description'] = clean_escaped_text(
                        cleaned_result['meta_data']['description']
                    )
            
            cleaned_results.append(cleaned_result)
        else:
            cleaned_results.append(result)
    
    return cleaned_results

def clean_chunks(chunks: list) -> list:
    """텍스트 청크들을 정리"""
    if not chunks:
        return chunks
    
    return [clean_escaped_text(chunk) if isinstance(chunk, str) else chunk for chunk in chunks]

def parse_and_clean_answer(answer_data: Union[str, Dict]) -> Dict[str, Any]:
    """answer 필드를 파싱하고 정리"""
    if isinstance(answer_data, str):
        try:
            # JSON 문자열인 경우 파싱 시도
            parsed_data = json.loads(answer_data)
            return clean_answer_dict(parsed_data)
        except json.JSONDecodeError:
            # JSON이 아닌 경우 단순 텍스트로 처리
            return {"answer": clean_escaped_text(answer_data)}
    elif isinstance(answer_data, dict):
        return clean_answer_dict(answer_data)
    else:
        return {"answer": str(answer_data)}

def clean_answer_dict(answer_dict: Dict[str, Any]) -> Dict[str, Any]:
    """answer 딕셔너리의 내용을 정리"""
    cleaned_dict = answer_dict.copy()
    
    # 메인 answer 텍스트 정리
    if 'answer' in cleaned_dict and isinstance(cleaned_dict['answer'], str):
        cleaned_dict['answer'] = clean_escaped_text(cleaned_dict['answer'])
        cleaned_dict['answer'] = format_markdown_links(cleaned_dict['answer'])
    
    # web_results 정리
    if 'web_results' in cleaned_dict:
        cleaned_dict['web_results'] = clean_web_results(cleaned_dict['web_results'])
    
    # chunks 정리
    if 'chunks' in cleaned_dict:
        cleaned_dict['chunks'] = clean_chunks(cleaned_dict['chunks'])
    
    # extra_web_results 정리
    if 'extra_web_results' in cleaned_dict:
        cleaned_dict['extra_web_results'] = clean_web_results(cleaned_dict['extra_web_results'])
    
    return cleaned_dict

def clean_perplexity_response(response: Dict[str, Any]) -> Dict[str, Any]:
    """Perplexity 응답 전체를 정리하는 메인 함수"""
    if not response:
        return response
    
    cleaned_response = response.copy()
    
    # text 배열이 있는 경우 처리
    if 'text' in cleaned_response and isinstance(cleaned_response['text'], list):
        for item in cleaned_response['text']:
            if isinstance(item, dict) and item.get('step_type') == 'FINAL':
                if 'content' in item and 'answer' in item['content']:
                    # FINAL 단계의 answer 정리
                    item['content']['answer'] = parse_and_clean_answer(item['content']['answer'])
    
    # 최상위 answer 필드가 있는 경우도 처리
    if 'answer' in cleaned_response:
        cleaned_response['answer'] = parse_and_clean_answer(cleaned_response['answer'])
    
    return cleaned_response

def is_complete_response(text: str) -> bool:
    """응답이 완전한지 확인하는 함수"""
    if not text or len(text) < 50:
        return False
    
    # |end_task| 마커가 있으면 완전한 응답으로 간주
    if "|end_task|" in text:
        return True
    
    # "..."으로 끝나는 경우 불완전한 응답으로 간주
    if text.strip().endswith("...") or text.strip().endswith("…"):
        return False
    
    # 일반적인 문장 종료 패턴이 있는지 확인
    sentence_endings = ['.', '!', '?', '다.', '요.', '습니다.', '됩니다.', '있습니다.']
    has_proper_ending = any(text.strip().endswith(ending) for ending in sentence_endings)
    
    # 충분한 길이와 적절한 종료가 있으면 완전한 응답으로 간주
    return len(text) > 100 and has_proper_ending

def extract_clean_answer(response: Dict[str, Any]) -> str:
    """응답에서 정리된 답변 텍스트만 추출"""
    try:
        # 1. formatted_response 내부의 text 객체에서 answer 찾기 (새로운 구조)
        if 'formatted_response' in response and isinstance(response['formatted_response'], dict):
            formatted_resp = response['formatted_response']
            
            # text 객체 내부에 answer가 직접 있는 경우
            if 'text' in formatted_resp and isinstance(formatted_resp['text'], dict):
                if 'answer' in formatted_resp['text']:
                    text = clean_escaped_text(formatted_resp['text']['answer'])
                    return format_markdown_links(text)
        
        # 2. 최상위 text 객체에서 answer 찾기
        if 'text' in response and isinstance(response['text'], dict):
            if 'answer' in response['text']:
                text = clean_escaped_text(response['text']['answer'])
                return format_markdown_links(text)
        
        # 3. text 배열에서 FINAL 단계 찾기 (기존 구조)
        if 'text' in response and isinstance(response['text'], list):
            for item in response['text']:
                if isinstance(item, dict) and item.get('step_type') == 'FINAL':
                    if 'content' in item and 'answer' in item['content']:
                        answer_content = item['content']['answer']
                        
                        # answer가 JSON 문자열인 경우
                        if isinstance(answer_content, str):
                            try:
                                parsed = json.loads(answer_content)
                                if 'answer' in parsed:
                                    text = clean_escaped_text(parsed['answer'])
                                    return format_markdown_links(text)
                            except json.JSONDecodeError:
                                text = clean_escaped_text(answer_content)
                                return format_markdown_links(text)
                        
                        # answer가 딕셔너리인 경우
                        elif isinstance(answer_content, dict) and 'answer' in answer_content:
                            text = clean_escaped_text(answer_content['answer'])
                            return format_markdown_links(text)
        
        # 4. formatted_response가 있는 경우 재귀적으로 탐색
        if 'formatted_response' in response:
            formatted_resp = response['formatted_response']
            if isinstance(formatted_resp, dict):
                # formatted_response 내부를 재귀적으로 검색
                recursive_result = extract_clean_answer(formatted_resp)
                if recursive_result != "답변을 찾을 수 없습니다.":
                    return recursive_result
        
        # 5. 최상위 answer 필드 확인
        if 'answer' in response:
            if isinstance(response['answer'], str):
                try:
                    parsed = json.loads(response['answer'])
                    if 'answer' in parsed:
                        text = clean_escaped_text(parsed['answer'])
                        return format_markdown_links(text)
                except json.JSONDecodeError:
                    text = clean_escaped_text(response['answer'])
                    return format_markdown_links(text)
            elif isinstance(response['answer'], dict) and 'answer' in response['answer']:
                text = clean_escaped_text(response['answer']['answer'])
                return format_markdown_links(text)
        
        # 6. clean_answer 필드 확인 (이미 정리된 답변)
        if 'clean_answer' in response and response['clean_answer'] != "답변을 찾을 수 없습니다.":
            return response['clean_answer']
        
        # 7. 새로운 응답 구조 처리 - 직접 text 필드에서 answer 추출
        if isinstance(response, dict):
            # 응답 객체 자체에서 answer 찾기
            for key, value in response.items():
                if key == 'answer' and isinstance(value, str) and value.strip():
                    text = clean_escaped_text(value)
                    return format_markdown_links(text)
                elif isinstance(value, dict) and 'answer' in value:
                    text = clean_escaped_text(value['answer'])
                    return format_markdown_links(text)
        
        return "답변을 찾을 수 없습니다."
    
    except Exception as e:
        return f"답변 파싱 중 오류가 발생했습니다: {str(e)}"

def convert_to_plain_text(text: str) -> str:
    """마크다운을 일반 텍스트로 변환"""
    if not text:
        return text
    
    # 마크다운 문법 제거
    text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)  # 볼드
    text = re.sub(r'\*(.*?)\*', r'\1', text)      # 이탤릭
    text = re.sub(r'#{1,6}\s', '', text)          # 헤더
    text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)  # 링크
    text = re.sub(r'`([^`]+)`', r'\1', text)      # 인라인 코드
    
    return text.strip()