import json
from typing import Callable, Iterator

from fastapi import HTTPException
from fastapi.responses import StreamingResponse

from app.services.ai import AIServiceError


def stream_ndjson(generator: Iterator[str], finalize: Callable[[str], dict]) -> StreamingResponse:
    """Turn a text-chunk generator into a newline-delimited JSON stream.

    Each line is one of:
      {"type": "chunk", "text": "..."}   - a piece of model output
      {"type": "done", ...fields}        - the final, parsed/saved result
      {"type": "error", "message": "..."} - generation failed mid-stream

    HTTP status codes can only be set before the first byte goes out, so the
    first chunk is fetched eagerly: a failure there (bad key already ruled
    out by the caller, rate limit, model unavailable, ...) still surfaces as
    a normal HTTPException. Once real output has started streaming, the
    response is already committed to 200 and a later failure is reported as
    an "error" frame instead.
    """
    try:
        first_chunk = next(generator, None)
    except AIServiceError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    def body():
        buffer: list[str] = []
        if first_chunk is not None:
            buffer.append(first_chunk)
            yield json.dumps({"type": "chunk", "text": first_chunk}) + "\n"
        try:
            for chunk in generator:
                buffer.append(chunk)
                yield json.dumps({"type": "chunk", "text": chunk}) + "\n"
        except AIServiceError as exc:
            yield json.dumps({"type": "error", "message": str(exc)}) + "\n"
            return

        result = finalize("".join(buffer))
        yield json.dumps({"type": "done", **result}) + "\n"

    return StreamingResponse(body(), media_type="application/x-ndjson")
