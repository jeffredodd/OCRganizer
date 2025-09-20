"""Direct HTTP client for LM Studio when OpenAI compatibility doesn't work."""
import logging

import requests

logger = logging.getLogger(__name__)


class LMStudioClient:
    """Direct HTTP client for LM Studio."""

    def __init__(self, base_url: str, model_name: str):
        """Initialize LM Studio client."""
        self.base_url = base_url.rstrip("/v1").rstrip("/")
        self.model_name = model_name

    def generate_response(self, prompt: str) -> str:
        """Generate response using LM Studio's direct API."""
        try:
            # Try the generate endpoint first
            url = f"{self.base_url}/api/generate"

            payload = {
                "model": self.model_name,
                "prompt": prompt,
                "max_tokens": 500,
                "temperature": 0.3,
                "stop": ["Human:", "User:", "\n\n"],
            }

            logger.info(f"Sending request to {url}")
            response = requests.post(url, json=payload, timeout=30)

            if response.status_code == 200:
                data = response.json()
                if "response" in data:
                    return data["response"]
                elif "text" in data:
                    return data["text"]
                elif "choices" in data and data["choices"]:
                    return data["choices"][0].get("text", "")

            # Try alternative endpoints
            return self._try_alternative_endpoints(prompt)

        except Exception as e:
            logger.error(f"LM Studio direct API error: {e}")
            return ""

    def _try_alternative_endpoints(self, prompt: str) -> str:
        """Try alternative LM Studio endpoints."""
        endpoints = ["/v1/completions", "/completions", "/api/v1/generate", "/generate"]

        for endpoint in endpoints:
            try:
                url = f"{self.base_url}{endpoint}"

                # Try different payload formats
                payloads = [
                    {
                        "model": self.model_name,
                        "prompt": prompt,
                        "max_tokens": 500,
                        "temperature": 0.3,
                    },
                    {"prompt": prompt, "max_tokens": 500, "temperature": 0.3},
                ]

                for payload in payloads:
                    logger.info(f"Trying endpoint: {url}")
                    response = requests.post(url, json=payload, timeout=30)

                    if response.status_code == 200:
                        data = response.json()

                        # Try different response formats
                        if "choices" in data and data["choices"]:
                            choice = data["choices"][0]
                            if "text" in choice:
                                return choice["text"]
                            elif "message" in choice and "content" in choice["message"]:
                                return choice["message"]["content"]

                        if "response" in data:
                            return data["response"]

                        if "text" in data:
                            return data["text"]

            except Exception as e:
                logger.debug(f"Endpoint {endpoint} failed: {e}")
                continue

        return ""
