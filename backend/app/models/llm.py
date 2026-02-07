"""Language Model handler using llama.cpp."""

import logging
import time
from pathlib import Path
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)


class LLMHandler:
    """Handler for language model inference using llama.cpp."""

    def __init__(
        self,
        model_name: str = "qwen2.5-1.5b-instruct",
        model_dir: Optional[Path] = None,
        n_ctx: int = 2048,
        n_gpu_layers: int = -1
    ):
        """
        Initialize the LLM handler.

        Args:
            model_name: Name of the model to load
            model_dir: Directory containing GGUF models
            n_ctx: Context window size
            n_gpu_layers: Number of layers to offload to GPU (-1 for all)
        """
        self.model_name = model_name
        self.model_dir = model_dir or Path(__file__).parent.parent.parent.parent / "models" / "llm"
        self.model_dir.mkdir(parents=True, exist_ok=True)
        self.n_ctx = n_ctx
        self.n_gpu_layers = n_gpu_layers
        self.model = None
        self._load_model()

    def _load_model(self):
        """Load the llama.cpp model."""
        try:
            from llama_cpp import Llama
            
            # Look for GGUF model file
            model_files = list(self.model_dir.glob("*.gguf"))
            
            if not model_files:
                logger.warning(f"No GGUF models found in {self.model_dir}")
                logger.info("Please download a GGUF model from Hugging Face")
                logger.info("Example: https://huggingface.co/Qwen/Qwen2.5-1.5B-Instruct-GGUF")
                # Create a dummy model flag
                self.model = None
                return
            
            # Use the first GGUF file found
            model_path = model_files[0]
            model_size_mb = model_path.stat().st_size / (1024 * 1024)
            logger.info(
                "Preparing to load LLM model: %s (%.1f MB)",
                model_path,
                model_size_mb
            )
            logger.info(
                "Loading LLM model into llama.cpp (ctx=%s, gpu_layers=%s)",
                self.n_ctx,
                self.n_gpu_layers
            )
            start_time = time.perf_counter()
            
            self.model = Llama(
                model_path=str(model_path),
                n_ctx=self.n_ctx,
                n_gpu_layers=self.n_gpu_layers,
                verbose=False
            )
            
            elapsed = time.perf_counter() - start_time
            logger.info(
                "LLM model loaded successfully in %.2fs: %s",
                elapsed,
                model_path.name
            )
            
        except ImportError:
            logger.error("llama-cpp-python not installed")
            self.model = None
        except Exception as e:
            logger.error(f"Failed to load LLM model: {e}")
            self.model = None

    def generate(
        self,
        messages: List[Dict[str, str]],
        max_tokens: int = 256,
        temperature: float = 0.7,
        top_p: float = 0.9,
        stop: Optional[List[str]] = None
    ) -> str:
        """
        Generate a response from the language model.

        Args:
            messages: List of message dictionaries with 'role' and 'content'
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            top_p: Nucleus sampling parameter
            stop: List of stop sequences

        Returns:
            Generated text response
        """
        if self.model is None:
            # Fallback response when model is not loaded
            logger.warning("LLM model not loaded, using fallback response")
            return self._generate_fallback_response(messages)
        
        try:
            response = self.model.create_chat_completion(
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
                top_p=top_p,
                stop=stop or []
            )
            
            generated_text = response["choices"][0]["message"]["content"]
            logger.info(f"Generated {len(generated_text)} characters")
            return generated_text
            
        except Exception as e:
            logger.error(f"Generation failed: {e}")
            return self._generate_fallback_response(messages)

    def _generate_fallback_response(self, messages: List[Dict[str, str]]) -> str:
        """Generate a fallback response when model is not available."""
        # Extract the last user message
        user_message = ""
        for msg in reversed(messages):
            if msg["role"] == "user":
                user_message = msg["content"]
                break
        
        # Simple rule-based responses for testing
        fallback_responses = {
            "hello": "¡Hola! Hello! I'm here to help you practice languages.",
            "how are you": "I'm doing well, thank you! ¿Cómo estás?",
            "goodbye": "¡Adiós! Goodbye! See you next time!",
            "help": "I can help you practice conversational phrases in various languages. Try greeting me or asking a question!",
        }
        
        user_lower = user_message.lower()
        for key, response in fallback_responses.items():
            if key in user_lower:
                return response
        
        return "I'm here to help you practice! (Note: Language model not loaded yet. Please download a GGUF model.)"

    def count_tokens(self, text: str) -> int:
        """Count tokens in text."""
        if self.model is None:
            # Rough approximation: ~4 chars per token
            return len(text) // 4
        
        try:
            tokens = self.model.tokenize(text.encode())
            return len(tokens)
        except Exception as e:
            logger.error(f"Token counting failed: {e}")
            return len(text) // 4
