FROM python:3.12-alpine AS build
RUN pip install uv && uv install tenint
RUN addgroup -S connector && adduser connector -S -G connector -h /connector

ADD --chown=connector:connector ./ /connector/

RUN uv pip install --system -r /connector/pyproject.toml

FROM build AS test
WORKDIR /connector/
RUN uv pip install --system "tenint[testing]" \
 && uv pip install --system --extra testing -r /connector/pyproject.toml
RUN ruff check
RUN python -m pytest

FROM build AS release
WORKDIR /connector/
ENTRYPOINT ["python", "connector.py"]
