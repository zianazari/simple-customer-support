import logging
from typing import TypeVar

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from openai import APIConnectionError, APIStatusError, APITimeoutError, AuthenticationError, RateLimitError
from pydantic import BaseModel

from app.config import get_settings

logger = logging.getLogger(__name__)
Schema = TypeVar("Schema", bound=BaseModel)


class LLMServiceError(Exception):
    """A safe error that can be returned from the HTTP boundary."""

    def __init__(self, message: str, status_code: int = 502) -> None:
        super().__init__(message)
        self.status_code = status_code


class EmailAnalyzer:
    """Typed OpenAI calls used by the workflow nodes."""

    def __init__(self) -> None:
        settings = get_settings()
        if not settings.openai_api_key:
            raise RuntimeError("OPENAI_API_KEY is not configured.")
        # Settings reads the repository-level .env file. Pass the value explicitly:
        # langchain-openai otherwise only looks at the process environment.
        self.model = ChatOpenAI(
            model=settings.openai_model,
            api_key=settings.openai_api_key,
            temperature=0,
            max_retries=2,
        )

    async def analyze(self, prompt: str, email: str, schema: type[Schema]) -> Schema:
        logger.info("Requesting structured model result: %s", schema.__name__)
        runnable = self.model.with_structured_output(schema, method="json_schema", strict=True)
        try:
            result = await runnable.ainvoke([
                SystemMessage(content=prompt),
                HumanMessage(content=email),
            ])
        except AuthenticationError as exc:
            logger.warning("OpenAI authentication failed")
            raise LLMServiceError("OpenAI rejected the API key. Check OPENAI_API_KEY and restart the backend.", 401) from exc
        except RateLimitError as exc:
            logger.warning("OpenAI rate limit reached")
            raise LLMServiceError("OpenAI rate limit reached. Please try again shortly.", 429) from exc
        except (APIConnectionError, APITimeoutError) as exc:
            logger.warning("OpenAI connection failed: %s", type(exc).__name__)
            raise LLMServiceError("Could not reach OpenAI. Check the network connection and try again.", 503) from exc
        except APIStatusError as exc:
            logger.warning("OpenAI returned status %s", exc.status_code)
            raise LLMServiceError(f"OpenAI could not process the request (status {exc.status_code}).", 502) from exc
        except Exception as exc:
            logger.exception("Structured model response failed")
            raise LLMServiceError("The AI response could not be parsed. Please try the email again.") from exc
        if not isinstance(result, schema):
            logger.error("Unexpected structured result type: %s", type(result).__name__)
            raise LLMServiceError("The AI returned an invalid structured response. Please try again.")
        return result
