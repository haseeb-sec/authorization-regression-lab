from fastapi import FastAPI

app = FastAPI(
    title="Authorization Regression Lab",
    description="A local learning lab for testing API authorization.",
    version="0.1.0",
)


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}
