"""
Tool Wrapper — Safe Call Layer with Observability
===================================================
Wraps every tool call with:
  1. Try/except for crash protection
  2. Standardized output format
  3. Fallback invocation on failure
  4. Source tracking (api vs fallback)
  5. Execution time tracing (Observability)

WHY: This is the SINGLE POINT OF CONTROL for all tool reliability.
     Instead of adding try/except inside every tool (messy, repeated),
     we wrap them here. If a tool crashes or returns an error, we
     automatically try the fallback and label the response honestly.

Usage:
    result = safe_call(
        tool_fn=weather_tool,
        tool_name="weather",
        fallback_fn=lambda: get_weather_fallback("Chennai"),
        location="Chennai"
    )
"""
import time
from server.utils.logger import get_logger

logger = get_logger("tool_wrapper")


def safe_call(tool_fn, tool_name: str, fallback_fn=None, **kwargs) -> dict:
    """
    Safely call a tool function with automatic fallback.

    Args:
        tool_fn:      The actual tool function to call
        tool_name:    Name of the tool (for logging/debugging)
        fallback_fn:  A callable that returns fallback data (no args)
        **kwargs:     Arguments to pass to tool_fn

    Returns:
        Standardized dict:
        {
            "success": True/False,
            "data": { ... },
            "error": "message" or None,
            "source": "api" | "fallback",
            "tool": "tool_name",
            "execution_time_ms": float
        }
    """
    start_time = time.time()

    # ---- Step 1: Try the real tool ----
    try:
        logger.info(f"[TRACE] Calling tool: {tool_name} with args: {list(kwargs.keys())}")
        result = tool_fn(**kwargs)

        # Check if the tool itself returned an error dict
        if isinstance(result, dict) and "error" in result:
            raise Exception(result["error"])

        elapsed_ms = round((time.time() - start_time) * 1000, 2)
        logger.info(f"[TRACE] Tool {tool_name} succeeded in {elapsed_ms}ms (source: api)")

        return {
            "success": True,
            "data": result,
            "error": None,
            "source": "api",
            "tool": tool_name,
            "execution_time_ms": elapsed_ms
        }

    except Exception as e:
        elapsed_ms = round((time.time() - start_time) * 1000, 2)
        logger.warning(f"[TRACE] Tool {tool_name} failed after {elapsed_ms}ms: {e}")

        # ---- Step 2: Try fallback ----
        if fallback_fn:
            try:
                fallback_start = time.time()
                fallback_data = fallback_fn()
                fallback_elapsed = round((time.time() - fallback_start) * 1000, 2)
                total_elapsed = round((time.time() - start_time) * 1000, 2)
                logger.info(f"[TRACE] Tool {tool_name} fallback succeeded in {fallback_elapsed}ms (total: {total_elapsed}ms)")

                return {
                    "success": True,
                    "data": fallback_data,
                    "error": None,
                    "source": "fallback",
                    "tool": tool_name,
                    "execution_time_ms": total_elapsed
                }
            except Exception as fallback_error:
                total_elapsed = round((time.time() - start_time) * 1000, 2)
                logger.error(f"[TRACE] Tool {tool_name} fallback also failed after {total_elapsed}ms: {fallback_error}")
                return {
                    "success": False,
                    "data": None,
                    "error": f"Tool failed: {str(e)} | Fallback also failed: {str(fallback_error)}",
                    "source": "none",
                    "tool": tool_name,
                    "execution_time_ms": total_elapsed
                }

        # ---- Step 3: No fallback available ----
        total_elapsed = round((time.time() - start_time) * 1000, 2)
        logger.error(f"[TRACE] Tool {tool_name} failed with no fallback after {total_elapsed}ms")
        return {
            "success": False,
            "data": None,
            "error": str(e),
            "source": "none",
            "tool": tool_name,
            "execution_time_ms": total_elapsed
        }
