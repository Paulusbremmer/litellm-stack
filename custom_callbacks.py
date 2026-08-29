import re
import litellm
from litellm.integrations.custom_logger import CustomLogger

# Comprehensive list of regex patterns for soft refusals
REFUSAL_PATTERNS = [
    r"cannot fulfill",
    r"unable to fulfill",
    r"cannot assist",
    r"unable to assist",
    r"cannot comply",
    r"unable to comply",
    r"cannot generate",
    r"unable to generate",
    r"cannot continue (this|with this)? roleplay",
    r"unable to continue (this|with this)? roleplay",
    r"cannot perform",
    r"must decline",
    r"against my safety",
    r"violates (my|safety) (guidelines|policy)",
    r"sorry, (but )?i cannot",
    r"sorry, (but )?i am unable",
    r"as an ai (language model)?, i (cannot|am unable)",
    r"i am not able to fulfill",
    r"i\'m not able to fulfill",
]

REFUSAL_REGEX = re.compile("|".join(REFUSAL_PATTERNS), re.IGNORECASE)

class RefusalInterceptor(CustomLogger):
    def _inspect_text_for_refusal(self, text: str, model: str):
        if text and REFUSAL_REGEX.search(text):
            raise litellm.APIError(
                status_code=400,
                message=f"Soft refusal detected in response text: {text[:100]}...",
                model=model,
                llm_provider="gemini",
            )

    async def async_log_success_event(self, kwargs, response_obj, start_time, end_time):
        """
        Inspects completed non-streaming response object for soft refusal phrases.
        """
        if response_obj and hasattr(response_obj, "choices") and response_obj.choices:
            for choice in response_obj.choices:
                content = ""
                if hasattr(choice, "message") and hasattr(choice.message, "content"):
                    content = choice.message.content or ""
                elif hasattr(choice, "delta") and hasattr(choice.delta, "content"):
                    content = choice.delta.content or ""

                self._inspect_text_for_refusal(content, kwargs.get("model", "unknown"))

    async def async_post_call_success_hook(self, data, user_api_key_dict, response):
        """
        Post-call proxy hook for inspecting raw response data before returning to client.
        """
        model = data.get("model", "unknown") if isinstance(data, dict) else "unknown"
        if isinstance(response, dict) and "choices" in response:
            for choice in response.get("choices", []):
                msg = choice.get("message", {}) or choice.get("delta", {})
                content = msg.get("content", "") or ""
                self._inspect_text_for_refusal(content, model)

refusal_interceptor = RefusalInterceptor()
