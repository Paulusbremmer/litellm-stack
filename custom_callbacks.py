import litellm
from litellm.integrations.custom_logger import CustomLogger

class RefusalInterceptor(CustomLogger):
    async def async_log_success_event(self, kwargs, response_obj, start_time, end_time):
        """
        Inspects model response content for soft refusal phrases.
        If a refusal phrase is detected, raises an APIError(status_code=400),
        forcing LiteLLM Router to trigger the fallback sequence.
        """
        if response_obj and hasattr(response_obj, "choices") and response_obj.choices:
            for choice in response_obj.choices:
                content = ""
                if hasattr(choice, "message") and hasattr(choice.message, "content"):
                    content = choice.message.content or ""
                elif hasattr(choice, "delta") and hasattr(choice.delta, "content"):
                    content = choice.delta.content or ""

                if content:
                    content_lower = content.lower()
                    refusal_patterns = [
                        "i cannot fulfill this request",
                        "i am unable to fulfill this request",
                        "i cannot assist with this request",
                        "i am sorry, but i cannot",
                        "i'm sorry, but i cannot",
                        "as an ai, i cannot fulfill",
                        "as an ai language model, i cannot",
                        "i am not able to fulfill this request",
                    ]
                    if any(pattern in content_lower for pattern in refusal_patterns):
                        raise litellm.APIError(
                            status_code=400,
                            message=f"Soft refusal detected in model response text: {content[:100]}...",
                            model=kwargs.get("model"),
                            llm_provider=kwargs.get("custom_llm_provider", "gemini"),
                        )

refusal_interceptor = RefusalInterceptor()
