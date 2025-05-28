#!/usr/bin/env python3
"""
AI 기능 확장 서비스 테스트 스크립트
각 기능을 테스트하고 예제를 확인할 수 있습니다.
"""

import asyncio
import httpx
import json
from typing import Dict, Any

class AIFeaturesTest:
    def __init__(self, base_url: str = "http://localhost:8001"):
        self.base_url = base_url
        
    async def test_connection(self):
        """서비스 연결 테스트"""
        print("🔌 서비스 연결 테스트 중...")
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.base_url}/health")
                if response.status_code == 200:
                    print("✅ 서비스 연결 성공!")
                    return True
                else:
                    print(f"❌ 서비스 연결 실패: {response.status_code}")
                    return False
        except Exception as e:
            print(f"❌ 연결 오류: {e}")
            return False
    
    async def test_youtube_summary(self):
        """YouTube 요약 기능 테스트"""
        print("\n📺 YouTube 요약 기능 테스트")
        print("=" * 50)
        
        test_cases = [
            {
                "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
                "summary_type": "brief",
                "language": "korean"
            },
            {
                "url": "https://youtu.be/jNQXAC9IVRw",
                "summary_type": "key_points",
                "language": "korean"
            }
        ]
        
        for i, test_case in enumerate(test_cases, 1):
            print(f"\n테스트 케이스 {i}:")
            print(f"URL: {test_case['url']}")
            print(f"요약 타입: {test_case['summary_type']}")
            
            try:
                async with httpx.AsyncClient(timeout=60) as client:
                    response = await client.post(
                        f"{self.base_url}/youtube/summary",
                        json=test_case
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        print("✅ 요약 생성 성공!")
                        print(f"요약 길이: {len(result['summary'])}자")
                        print("요약 미리보기:", result['summary'][:200] + "...")
                    else:
                        print(f"❌ 요약 실패: {response.status_code}")
                        print(response.text)
                        
            except Exception as e:
                print(f"❌ 오류: {e}")
    
    async def test_blog_creation(self):
        """블로그 생성 기능 테스트"""
        print("\n📝 블로그 생성 기능 테스트")
        print("=" * 50)
        
        test_cases = [
            {
                "keyword": "인공지능과 미래",
                "target_audience": "일반인",
                "post_length": "medium",
                "include_seo": True
            },
            {
                "keyword": "건강한 아침 루틴",
                "target_audience": "직장인",
                "post_length": "short",
                "include_seo": False
            }
        ]
        
        for i, test_case in enumerate(test_cases, 1):
            print(f"\n테스트 케이스 {i}:")
            print(f"키워드: {test_case['keyword']}")
            print(f"대상 독자: {test_case['target_audience']}")
            
            try:
                async with httpx.AsyncClient(timeout=120) as client:
                    response = await client.post(
                        f"{self.base_url}/blog/create",
                        json=test_case
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        print("✅ 블로그 포스트 생성 성공!")
                        print(f"포스트 길이: {len(result['blog_post'])}자")
                        print("포스트 미리보기:", result['blog_post'][:200] + "...")
                    else:
                        print(f"❌ 블로그 생성 실패: {response.status_code}")
                        print(response.text)
                        
            except Exception as e:
                print(f"❌ 오류: {e}")
    
    async def test_news_analysis(self):
        """뉴스 분석 기능 테스트"""
        print("\n📰 뉴스 분석 기능 테스트")
        print("=" * 50)
        
        test_cases = [
            {
                "topic": "한국 경제",
                "date_range": "recent",
                "analysis_type": "summary"
            },
            {
                "topic": "기후 변화",
                "date_range": "week",
                "analysis_type": "trend"
            }
        ]
        
        for i, test_case in enumerate(test_cases, 1):
            print(f"\n테스트 케이스 {i}:")
            print(f"주제: {test_case['topic']}")
            print(f"분석 타입: {test_case['analysis_type']}")
            
            try:
                async with httpx.AsyncClient(timeout=90) as client:
                    response = await client.post(
                        f"{self.base_url}/news/analyze",
                        json=test_case
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        print("✅ 뉴스 분석 성공!")
                        print(f"분석 길이: {len(result['analysis'])}자")
                        print("분석 미리보기:", result['analysis'][:200] + "...")
                    else:
                        print(f"❌ 뉴스 분석 실패: {response.status_code}")
                        print(response.text)
                        
            except Exception as e:
                print(f"❌ 오류: {e}")
    
    async def test_study_material(self):
        """학습 자료 생성 기능 테스트"""
        print("\n📚 학습 자료 생성 기능 테스트")
        print("=" * 50)
        
        test_cases = [
            {
                "subject": "파이썬 프로그래밍",
                "level": "beginner",
                "format_type": "guide"
            },
            {
                "subject": "머신러닝 기초",
                "level": "intermediate",
                "format_type": "quiz"
            }
        ]
        
        for i, test_case in enumerate(test_cases, 1):
            print(f"\n테스트 케이스 {i}:")
            print(f"주제: {test_case['subject']}")
            print(f"난이도: {test_case['level']}")
            print(f"형식: {test_case['format_type']}")
            
            try:
                async with httpx.AsyncClient(timeout=90) as client:
                    response = await client.post(
                        f"{self.base_url}/study/create",
                        json=test_case
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        print("✅ 학습 자료 생성 성공!")
                        print(f"자료 길이: {len(result['study_material'])}자")
                        print("자료 미리보기:", result['study_material'][:200] + "...")
                    else:
                        print(f"❌ 학습 자료 생성 실패: {response.status_code}")
                        print(response.text)
                        
            except Exception as e:
                print(f"❌ 오류: {e}")
    
    async def test_website_analysis(self):
        """웹사이트 분석 기능 테스트"""
        print("\n🌐 웹사이트 분석 기능 테스트")
        print("=" * 50)
        
        test_cases = [
            {
                "url": "https://www.google.com",
                "analysis_type": "content"
            },
            {
                "url": "https://github.com",
                "analysis_type": "user_experience"
            }
        ]
        
        for i, test_case in enumerate(test_cases, 1):
            print(f"\n테스트 케이스 {i}:")
            print(f"URL: {test_case['url']}")
            print(f"분석 타입: {test_case['analysis_type']}")
            
            try:
                async with httpx.AsyncClient(timeout=90) as client:
                    response = await client.post(
                        f"{self.base_url}/website/analyze",
                        json=test_case
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        print("✅ 웹사이트 분석 성공!")
                        print(f"분석 길이: {len(result['analysis'])}자")
                        print("분석 미리보기:", result['analysis'][:200] + "...")
                    else:
                        print(f"❌ 웹사이트 분석 실패: {response.status_code}")
                        print(response.text)
                        
            except Exception as e:
                print(f"❌ 오류: {e}")
    
    async def test_creative_content(self):
        """창작 도우미 기능 테스트"""
        print("\n🎨 창작 도우미 기능 테스트")
        print("=" * 50)
        
        test_cases = [
            {
                "content_type": "story",
                "theme": "우주 여행",
                "tone": "emotional",
                "length": "short"
            },
            {
                "content_type": "poem",
                "theme": "봄의 전령",
                "tone": "casual",
                "length": "medium"
            }
        ]
        
        for i, test_case in enumerate(test_cases, 1):
            print(f"\n테스트 케이스 {i}:")
            print(f"콘텐츠 타입: {test_case['content_type']}")
            print(f"주제: {test_case['theme']}")
            print(f"톤: {test_case['tone']}")
            
            try:
                async with httpx.AsyncClient(timeout=90) as client:
                    response = await client.post(
                        f"{self.base_url}/creative/generate",
                        json=test_case
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        print("✅ 창작 콘텐츠 생성 성공!")
                        print(f"콘텐츠 길이: {len(result['creative_content'])}자")
                        print("콘텐츠 미리보기:", result['creative_content'][:200] + "...")
                    else:
                        print(f"❌ 창작 콘텐츠 생성 실패: {response.status_code}")
                        print(response.text)
                        
            except Exception as e:
                print(f"❌ 오류: {e}")
    
    async def run_all_tests(self):
        """모든 테스트 실행"""
        print("🚀 AI 기능 확장 서비스 전체 테스트 시작")
        print("=" * 60)
        
        # 연결 테스트
        if not await self.test_connection():
            print("\n❌ 서비스에 연결할 수 없습니다. features.py가 실행 중인지 확인하세요.")
            return
        
        # 각 기능 테스트
        test_functions = [
            self.test_youtube_summary,
            self.test_blog_creation,
            self.test_news_analysis,
            self.test_study_material,
            self.test_website_analysis,
            self.test_creative_content
        ]
        
        for test_func in test_functions:
            try:
                await test_func()
                await asyncio.sleep(2)  # 요청 간격 조절
            except KeyboardInterrupt:
                print("\n⏹️ 사용자에 의해 테스트가 중단되었습니다.")
                break
            except Exception as e:
                print(f"\n❌ 테스트 중 오류 발생: {e}")
        
        print("\n🏁 전체 테스트 완료!")

async def interactive_test():
    """대화형 테스트 모드"""
    tester = AIFeaturesTest()
    
    while True:
        print("\n" + "=" * 60)
        print("🤖 AI 기능 확장 서비스 테스트")
        print("=" * 60)
        print("1. 🔌 연결 테스트")
        print("2. 📺 YouTube 요약 테스트")
        print("3. 📝 블로그 생성 테스트")
        print("4. 📰 뉴스 분석 테스트")
        print("5. 📚 학습 자료 생성 테스트")
        print("6. 🌐 웹사이트 분석 테스트")
        print("7. 🎨 창작 도우미 테스트")
        print("8. 🚀 전체 테스트 실행")
        print("9. ❌ 종료")
        
        choice = input("\n선택하세요 (1-9): ").strip()
        
        try:
            if choice == "1":
                await tester.test_connection()
            elif choice == "2":
                await tester.test_youtube_summary()
            elif choice == "3":
                await tester.test_blog_creation()
            elif choice == "4":
                await tester.test_news_analysis()
            elif choice == "5":
                await tester.test_study_material()
            elif choice == "6":
                await tester.test_website_analysis()
            elif choice == "7":
                await tester.test_creative_content()
            elif choice == "8":
                await tester.run_all_tests()
            elif choice == "9":
                print("👋 테스트를 종료합니다.")
                break
            else:
                print("❌ 올바른 번호를 선택해주세요.")
                
        except KeyboardInterrupt:
            print("\n⏹️ 테스트가 중단되었습니다.")
        except Exception as e:
            print(f"\n❌ 오류 발생: {e}")
        
        input("\n계속하려면 Enter를 누르세요...")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--auto":
        # 자동 모드: 모든 테스트 실행
        asyncio.run(AIFeaturesTest().run_all_tests())
    else:
        # 대화형 모드
        asyncio.run(interactive_test())