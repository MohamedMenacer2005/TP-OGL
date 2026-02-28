"""
LLM Client Utility for Agent Integration
Provides interface to Groq API for semantic code analysis and generation.
"""

import os
from typing import Optional, Dict, Any
import logging
from src.utils.prompt_manager import PromptManager

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()

try:
    from groq import Groq
except ImportError:
    Groq = None


logger = logging.getLogger(__name__)


class LLMClient:
    """
    Client for interacting with Groq API.
    Handles API initialization and request execution.
    """
    
    def __init__(self, model: str = "llama-3.3-70b-versatile", api_key: Optional[str] = None):
        """
        Initialize LLM client.
        
        Args:
            model: Model name (default: llama-3.3-70b-versatile)
            api_key: Optional API key (reads from GROQ_API_KEY env if not provided)
            
        Raises:
            RuntimeError: If groq not installed or API key missing
            ValueError: If API key is empty
        """
        if Groq is None:
            raise RuntimeError(
                "groq not installed. "
                "Install with: pip install groq"
            )
        
        self.model = model
        
        # Get API key
        api_key = api_key or os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError(
                "GROQ_API_KEY not found. Set environment variable or pass api_key parameter."
            )
        
        if not api_key.strip():
            raise ValueError("API key is empty")
        
        # Configure API
        try:
            self.client = Groq(api_key=api_key)
            logger.info(f"Initialized LLM client with model: {model}")
        except Exception as e:
            logger.error(f"Failed to initialize LLM client: {e}")
            raise RuntimeError(f"LLM initialization failed: {e}") from e

        self.prompt_manager = PromptManager()
    
    def generate_correction(self, 
                          code: str, 
                          issue: str,
                          context: str = "") -> str:
        """
        Generate semantic correction for code issue.
        
        Args:
            code: Python code to fix
            issue: Description of issue to fix
            context: Optional additional context
            
        Returns:
            Corrected code
            
        Raises:
            RuntimeError: If LLM call fails
            ValueError: If inputs are invalid
        """
        if not code or not code.strip():
            raise ValueError("Code cannot be empty")
        
        if not issue or not issue.strip():
            raise ValueError("Issue cannot be empty")
        
        prompt = self.prompt_manager.format(
            "llm_correction",
            code=code[:2000],
            issue=issue,
            context=context or ""
        )
        
        try:
            logger.debug(f"Sending correction request to LLM for issue: {issue}")
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=1024,
                temperature=0.3,
            )
            
            if not response or not response.choices:
                raise RuntimeError("LLM returned empty response")
            
            # Extract code block from response
            corrected = response.choices[0].message.content.strip()
            if corrected.endswith("```"):
                corrected = corrected[:-3].strip()
            
            logger.debug(f"LLM generated correction ({len(corrected)} chars)")
            return corrected
        
        except Exception as e:
            logger.error(f"LLM correction failed: {e}")
            raise RuntimeError(f"Failed to generate correction: {e}") from e
    
    def analyze_code_quality(self, code: str) -> Dict[str, Any]:
        """
        Analyze code quality using LLM.
        
        Args:
            code: Python code to analyze
            
        Returns:
            Dict with quality analysis results
            
        Raises:
            RuntimeError: If LLM call fails
        """
        if not code or not code.strip():
            raise ValueError("Code cannot be empty")
        
        prompt = self.prompt_manager.format(
            "llm_quality",
            code=code[:2000]
        )
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=512,
                temperature=0.2,
            )
            
            if not response or not response.choices:
                raise RuntimeError("LLM returned empty response")
            
            # Parse JSON response
            import json
            text = response.choices[0].message.content.strip()
            # Remove markdown code blocks if present
            if text.startswith("```"):
                text = text.split("```")[1]
                if text.startswith("json"):
                    text = text[4:]
            text = text.strip()
            
            result = json.loads(text)
            logger.debug(f"LLM analysis returned: {result}")
            return result
        
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM response as JSON: {e}")
            raise RuntimeError(f"Invalid JSON response from LLM: {e}") from e
        except Exception as e:
            logger.error(f"LLM analysis failed: {e}")
            raise RuntimeError(f"Failed to analyze code: {e}") from e
    
    def suggest_improvements(self, code: str, max_suggestions: int = 3) -> list:
        """
        Get LLM suggestions for code improvements.
        
        Args:
            code: Python code to analyze
            max_suggestions: Maximum number of suggestions
            
        Returns:
            List of improvement suggestions
            
        Raises:
            RuntimeError: If LLM call fails
        """
        if not code or not code.strip():
            raise ValueError("Code cannot be empty")
        
        prompt = self.prompt_manager.format(
            "llm_suggestions",
            max_suggestions=str(max_suggestions),
            code=code[:2000]
        )
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=512,
                temperature=0.2,
            )
            
            if not response or not response.choices:
                return []
            
            import json
            text = response.choices[0].message.content.strip()
            if text.startswith("```"):
                text = text.split("```")[1]
                if text.startswith("json"):
                    text = text[4:]
            text = text.strip()
            
            suggestions = json.loads(text)
            logger.debug(f"LLM suggested {len(suggestions)} improvements")
            return suggestions[:max_suggestions]
        
        except (json.JSONDecodeError, Exception) as e:
            logger.warning(f"Failed to get LLM suggestions: {e}")
            return []
