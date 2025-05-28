"""
Perplexity AI Features 2 - All Available Features without Registration
Based on: https://github.com/helallao/perplexity-ai
"""

import asyncio
import os
import json
import time
from typing import Optional, List, Dict, Any, AsyncGenerator
import base64
import mimetypes
from perplexity_async import PerplexityAsync
from perplexity import Perplexity

class PerplexityFeatures2:
    def __init__(self, session_id: Optional[str] = None):
        """
        Initialize Perplexity client without registration
        """
        self.sync_client = Perplexity()
        self.async_client = PerplexityAsync()
        self.session_id = session_id
        
    def search(self, query: str, mode: str = "concise") -> str:
        """
        Basic search functionality
        
        Args:
            query: Search query
            mode: Response mode - "concise", "informative", or "creative"
        """
        try:
            response = self.sync_client.search(query, mode=mode)
            return response
        except Exception as e:
            return f"Search error: {str(e)}"
    
    async def async_search(self, query: str, mode: str = "concise") -> str:
        """
        Asynchronous search functionality
        
        Args:
            query: Search query
            mode: Response mode - "concise", "informative", or "creative"
        """
        try:
            response = await self.async_client.search(query, mode=mode)
            return response
        except Exception as e:
            return f"Async search error: {str(e)}"
    
    def chat(self, message: str, conversation_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Chat functionality with conversation tracking
        
        Args:
            message: Chat message
            conversation_id: Optional conversation ID to continue chat
        """
        try:
            response = self.sync_client.chat(message, conversation_id=conversation_id)
            return {
                "response": response.get("answer", ""),
                "conversation_id": response.get("conversation_id"),
                "sources": response.get("sources", [])
            }
        except Exception as e:
            return {"error": f"Chat error: {str(e)}"}
    
    async def async_chat(self, message: str, conversation_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Asynchronous chat functionality
        
        Args:
            message: Chat message
            conversation_id: Optional conversation ID to continue chat
        """
        try:
            response = await self.async_client.chat(message, conversation_id=conversation_id)
            return {
                "response": response.get("answer", ""),
                "conversation_id": response.get("conversation_id"),
                "sources": response.get("sources", [])
            }
        except Exception as e:
            return {"error": f"Async chat error: {str(e)}"}
    
    def stream_search(self, query: str, mode: str = "concise"):
        """
        Streaming search for real-time responses
        
        Args:
            query: Search query
            mode: Response mode
        """
        try:
            for chunk in self.sync_client.stream_search(query, mode=mode):
                yield chunk
        except Exception as e:
            yield f"Stream error: {str(e)}"
    
    async def async_stream_search(self, query: str, mode: str = "concise") -> AsyncGenerator[str, None]:
        """
        Asynchronous streaming search
        
        Args:
            query: Search query
            mode: Response mode
        """
        try:
            async for chunk in self.async_client.stream_search(query, mode=mode):
                yield chunk
        except Exception as e:
            yield f"Async stream error: {str(e)}"
    
    def upload_image(self, image_path: str, description: str = "") -> Dict[str, Any]:
        """
        Upload and analyze image
        
        Args:
            image_path: Path to image file
            description: Optional description or query about the image
        """
        try:
            if not os.path.exists(image_path):
                return {"error": "Image file not found"}
            
            # Read and encode image
            with open(image_path, 'rb') as f:
                image_data = f.read()
            
            # Get MIME type
            mime_type, _ = mimetypes.guess_type(image_path)
            if not mime_type or not mime_type.startswith('image/'):
                return {"error": "Invalid image file type"}
            
            # Encode to base64
            image_b64 = base64.b64encode(image_data).decode('utf-8')
            
            response = self.sync_client.upload_image(image_b64, description)
            return {
                "analysis": response.get("answer", ""),
                "image_id": response.get("image_id"),
                "sources": response.get("sources", [])
            }
        except Exception as e:
            return {"error": f"Image upload error: {str(e)}"}
    
    async def async_upload_image(self, image_path: str, description: str = "") -> Dict[str, Any]:
        """
        Asynchronous image upload and analysis
        
        Args:
            image_path: Path to image file
            description: Optional description or query about the image
        """
        try:
            if not os.path.exists(image_path):
                return {"error": "Image file not found"}
            
            with open(image_path, 'rb') as f:
                image_data = f.read()
            
            mime_type, _ = mimetypes.guess_type(image_path)
            if not mime_type or not mime_type.startswith('image/'):
                return {"error": "Invalid image file type"}
            
            image_b64 = base64.b64encode(image_data).decode('utf-8')
            
            response = await self.async_client.upload_image(image_b64, description)
            return {
                "analysis": response.get("answer", ""),
                "image_id": response.get("image_id"),
                "sources": response.get("sources", [])
            }
        except Exception as e:
            return {"error": f"Async image upload error: {str(e)}"}
    
    def upload_file(self, file_path: str, query: str = "") -> Dict[str, Any]:
        """
        Upload and analyze file (PDF, DOC, TXT, etc.)
        
        Args:
            file_path: Path to file
            query: Query about the file content
        """
        try:
            if not os.path.exists(file_path):
                return {"error": "File not found"}
            
            with open(file_path, 'rb') as f:
                file_data = f.read()
            
            # Get MIME type
            mime_type, _ = mimetypes.guess_type(file_path)
            
            # Encode to base64
            file_b64 = base64.b64encode(file_data).decode('utf-8')
            
            response = self.sync_client.upload_file(file_b64, query, mime_type=mime_type)
            return {
                "analysis": response.get("answer", ""),
                "file_id": response.get("file_id"),
                "sources": response.get("sources", [])
            }
        except Exception as e:
            return {"error": f"File upload error: {str(e)}"}
    
    def generate_image(self, prompt: str, style: str = "realistic") -> Dict[str, Any]:
        """
        Generate image using AI
        
        Args:
            prompt: Image generation prompt
            style: Image style - "realistic", "artistic", "cartoon", etc.
        """
        try:
            response = self.sync_client.generate_image(prompt, style=style)
            return {
                "image_url": response.get("image_url"),
                "image_id": response.get("image_id"),
                "prompt_used": response.get("prompt_used", prompt)
            }
        except Exception as e:
            return {"error": f"Image generation error: {str(e)}"}
    
    async def async_generate_image(self, prompt: str, style: str = "realistic") -> Dict[str, Any]:
        """
        Asynchronous image generation
        
        Args:
            prompt: Image generation prompt
            style: Image style
        """
        try:
            response = await self.async_client.generate_image(prompt, style=style)
            return {
                "image_url": response.get("image_url"),
                "image_id": response.get("image_id"),
                "prompt_used": response.get("prompt_used", prompt)
            }
        except Exception as e:
            return {"error": f"Async image generation error: {str(e)}"}
    
    def get_conversation_history(self, conversation_id: str) -> List[Dict[str, Any]]:
        """
        Get conversation history
        
        Args:
            conversation_id: Conversation ID
        """
        try:
            history = self.sync_client.get_conversation_history(conversation_id)
            return history
        except Exception as e:
            return [{"error": f"History retrieval error: {str(e)}"}]
    
    def delete_conversation(self, conversation_id: str) -> bool:
        """
        Delete a conversation
        
        Args:
            conversation_id: Conversation ID to delete
        """
        try:
            result = self.sync_client.delete_conversation(conversation_id)
            return result
        except Exception as e:
            print(f"Delete conversation error: {str(e)}")
            return False
    
    def search_with_filters(self, query: str, filters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Search with additional filters
        
        Args:
            query: Search query
            filters: Dictionary with filters like date_range, sources, etc.
        """
        try:
            response = self.sync_client.search_with_filters(query, filters=filters)
            return {
                "answer": response.get("answer", ""),
                "sources": response.get("sources", []),
                "filters_applied": filters
            }
        except Exception as e:
            return {"error": f"Filtered search error: {str(e)}"}
    
    def summarize_url(self, url: str) -> Dict[str, Any]:
        """
        Summarize content from URL
        
        Args:
            url: URL to summarize
        """
        try:
            response = self.sync_client.summarize_url(url)
            return {
                "summary": response.get("summary", ""),
                "title": response.get("title", ""),
                "url": url,
                "sources": response.get("sources", [])
            }
        except Exception as e:
            return {"error": f"URL summarization error: {str(e)}"}
    
    def multi_query_search(self, queries: List[str]) -> List[Dict[str, Any]]:
        """
        Perform multiple searches at once
        
        Args:
            queries: List of search queries
        """
        results = []
        for query in queries:
            try:
                response = self.sync_client.search(query)
                results.append({
                    "query": query,
                    "answer": response,
                    "status": "success"
                })
            except Exception as e:
                results.append({
                    "query": query,
                    "error": str(e),
                    "status": "error"
                })
        return results
    
    async def async_multi_query_search(self, queries: List[str]) -> List[Dict[str, Any]]:
        """
        Asynchronous multiple search queries
        
        Args:
            queries: List of search queries
        """
        tasks = []
        for query in queries:
            tasks.append(self.async_search(query))
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        formatted_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                formatted_results.append({
                    "query": queries[i],
                    "error": str(result),
                    "status": "error"
                })
            else:
                formatted_results.append({
                    "query": queries[i],
                    "answer": result,
                    "status": "success"
                })
        
        return formatted_results
    
    def save_conversation_to_file(self, conversation_id: str, file_path: str) -> bool:
        """
        Save conversation to JSON file
        
        Args:
            conversation_id: Conversation ID
            file_path: Path to save file
        """
        try:
            history = self.get_conversation_history(conversation_id)
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(history, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Save conversation error: {str(e)}")
            return False
    
    def get_available_models(self) -> List[str]:
        """
        Get list of available AI models
        """
        try:
            models = self.sync_client.get_available_models()
            return models
        except Exception as e:
            return [f"Error getting models: {str(e)}"]
    
    def set_model(self, model_name: str) -> bool:
        """
        Set the AI model to use
        
        Args:
            model_name: Name of the model to use
        """
        try:
            result = self.sync_client.set_model(model_name)
            return result
        except Exception as e:
            print(f"Set model error: {str(e)}")
            return False


# Example usage functions
def demo_basic_features():
    """Demonstrate basic features"""
    client = PerplexityFeatures2()
    
    print("=== Basic Search ===")
    result = client.search("What is artificial intelligence?")
    print(result[:200] + "..." if len(result) > 200 else result)
    
    print("\n=== Chat Feature ===")
    chat_result = client.chat("Explain quantum computing in simple terms")
    print(f"Response: {chat_result.get('response', '')[:200]}...")
    print(f"Conversation ID: {chat_result.get('conversation_id')}")
    
    print("\n=== Multiple Queries ===")
    queries = ["Current weather in Seoul", "Latest AI news", "Best programming languages 2024"]
    multi_results = client.multi_query_search(queries)
    for result in multi_results:
        print(f"Query: {result['query']}")
        print(f"Status: {result['status']}")
        if result['status'] == 'success':
            print(f"Answer: {result['answer'][:100]}...")
        print()

def demo_file_features():
    """Demonstrate file and image features"""
    client = PerplexityFeatures2()
    
    # Example for image upload (uncomment when you have an image)
    # print("=== Image Analysis ===")
    # image_result = client.upload_image("path/to/your/image.jpg", "What do you see in this image?")
    # print(image_result)
    
    # Example for file upload (uncomment when you have a file)
    # print("=== File Analysis ===")
    # file_result = client.upload_file("path/to/your/document.pdf", "Summarize this document")
    # print(file_result)
    
    print("=== Image Generation ===")
    gen_result = client.generate_image("A beautiful sunset over mountains", style="realistic")
    print(gen_result)

async def demo_async_features():
    """Demonstrate async features"""
    client = PerplexityFeatures2()
    
    print("=== Async Search ===")
    result = await client.async_search("Future of renewable energy")
    print(result[:200] + "..." if len(result) > 200 else result)
    
    print("\n=== Async Multiple Queries ===")
    queries = ["Space exploration 2024", "Climate change solutions", "AI in healthcare"]
    results = await client.async_multi_query_search(queries)
    for result in results:
        print(f"Query: {result['query']} - Status: {result['status']}")

if __name__ == "__main__":
    print("Perplexity AI Features 2 - All Features Demo")
    print("=" * 50)
    
    # Run basic demos
    demo_basic_features()
    demo_file_features()
    
    # Run async demo
    print("\n=== Async Features Demo ===")
    asyncio.run(demo_async_features())