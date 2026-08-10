"""LLM service for Mesh API integration (all LLM calls)."""
from typing import Optional, List, Dict, Any
import os
from openai import OpenAI
import json

from src.logging_config.config import get_logger

logger = get_logger(__name__)


class LLMService:
    """Service for interacting with LLMs through Mesh API."""

    def __init__(self):
        """Initialize Mesh API client."""
        api_key = os.getenv("MESH_API_KEY")
        if not api_key:
            raise ValueError("MESH_API_KEY not configured. Add it to .env file.")
        
        self.client = OpenAI(
            base_url="https://api.meshapi.ai/v1",
            api_key=api_key
        )
        self.default_model = os.getenv("LLM_MODEL", "openai/gpt-4o")
        self.temperature = float(os.getenv("LLM_TEMPERATURE", "0.7"))

    def generate_text(self, prompt: str, temperature: Optional[float] = None, max_tokens: int = 500) -> str:
        """Generate text using LLM."""
        try:
            temp = temperature if temperature is not None else self.temperature
            
            response = self.client.chat.completions.create(
                model=self.default_model,
                messages=[
                    {"role": "system", "content": "You are a helpful AI assistant."},
                    {"role": "user", "content": prompt}
                ],
                temperature=temp,
                max_tokens=max_tokens,
            )
            
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Error calling LLM: {e}")
            raise

    def build_search_query(self, user_context: str, interests: List[str]) -> str:
        """Generate semantic search query from user context."""
        prompt = f"""
Based on the following user activity and interests, generate a concise semantic search query
that would help find the most relevant products/courses for this user.

User Context:
{user_context}

User Interests:
{', '.join(interests)}

Return only the search query, no additional explanation.
        """
        
        return self.generate_text(prompt, max_tokens=200)

    def generate_recommendation_narrative(
        self,
        user_name: str,
        user_interests: List[str],
        recommended_products: List[Dict[str, Any]],
        context: str
    ) -> str:
        """Generate personalized, persuasive recommendation narrative."""
        products_text = "\n".join([
            f"- {p.get('name')}: {p.get('description', '')} (Price: ${p.get('price', 0)})"
            for p in recommended_products[:5]  # Top 5 products
        ])
        
        prompt = f"""
Create a persuasive, personalized recommendation message for {user_name}.

User's interests and activity:
{context}

Key topics they care about: {', '.join(user_interests)}

Recommended courses/products:
{products_text}

Write a compelling 2-3 sentence message that:
1. Acknowledges their specific learning journey
2. Explains why these products are perfect for them
3. Motivates them to take action

Make it personal, warm, and convincing. No marketing jargon.
        """
        
        return self.generate_text(prompt, temperature=0.7, max_tokens=300)

    def evaluate_retrieval_quality(self, query: str, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Evaluate if retrieval results are good quality."""
        results_text = "\n".join([
            f"- {r.get('name')}: {r.get('score', 0):.2f}"
            for r in results[:5]
        ])
        
        prompt = f"""
Evaluate if these search results are good matches for the query: "{query}"

Results:
{results_text}

Respond with JSON:
{{
  "quality_score": <0-1>,
  "is_good_match": <true/false>,
  "reasoning": "<why or why not>"
}}
        """
        
        try:
            response_text = self.generate_text(prompt, temperature=0.2, max_tokens=200)
            # Extract JSON from response
            response_json = json.loads(response_text)
            return response_json
        except Exception as e:
            logger.error(f"Error evaluating retrieval quality: {e}")
            return {
                "quality_score": 0.5,
                "is_good_match": len(results) > 0,
                "reasoning": "Could not evaluate quality"
            }

    def refine_search_query(self, original_query: str, feedback: str) -> str:
        """Refine search query based on feedback."""
        prompt = f"""
The semantic search with this query returned poor results: "{original_query}"

Feedback: {feedback}

Generate an improved, more specific search query that will find better matches.
Return only the refined query.
        """
        
        return self.generate_text(prompt, temperature=0.5, max_tokens=150)

    def extract_user_interests(self, activity_context: str) -> List[str]:
        """Extract key interests from user activity."""
        prompt = f"""
Based on the user's activity, extract 3-5 key learning interests or topics they care about.

Activity context:
{activity_context}

Return as a comma-separated list of interests, nothing else.
Example output: Machine Learning, Python, Data Science, Statistics, Deep Learning
        """
        
        response = self.generate_text(prompt, temperature=0.3, max_tokens=100)
        interests = [i.strip() for i in response.split(",")]
        return interests

    def generate_email_subject(self, user_name: str, key_topics: List[str]) -> str:
        """Generate an engaging email subject line."""
        topics = ", ".join(key_topics[:2])
        
        prompt = f"""
Generate a compelling email subject line for {user_name}'s daily learning digest about: {topics}

Make it engaging and curiosity-inducing. Keep it under 60 characters.
Return only the subject line.
        """
        
        return self.generate_text(prompt, temperature=0.8, max_tokens=50)
