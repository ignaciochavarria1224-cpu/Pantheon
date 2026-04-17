from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import threading
import uvicorn

from core.brain import chat
from core.memory import (
    initialize_database,
    get_recent_conversations,
    get_decisions,
    get_active_patterns,
    clear_session_rules,
)
from core.mind import get_vault_snapshot
from pantheon.api import (
    get_activity_snapshot,
    get_blackbook_snapshot,
    get_doctor_snapshot,
    get_maridian_snapshot,
    get_olympus_snapshot,
    get_overview_snapshot,
    reason,
)
from pantheon.services import blackbook, maridian

# Initialize on startup
initialize_database()
clear_session_rules()


def start_brief_scheduler_thread():
    try:
        from agents.brief import start_brief_scheduler

        start_brief_scheduler()
    except Exception:
        return


brief_thread = threading.Thread(target=start_brief_scheduler_thread, daemon=True)
brief_thread.start()


def start_trigger_scheduler():
    try:
        import schedule
        import time
        from core.triggers import run_all_triggers

        schedule.every(1).hours.do(run_all_triggers)
        while True:
            schedule.run_pending()
            time.sleep(60)
    except Exception:
        return


trigger_thread = threading.Thread(target=start_trigger_scheduler, daemon=True)
trigger_thread.start()

app = FastAPI(title="Apollo", version="3.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

conversation_history = []


class ChatRequest(BaseModel):
    message: str
    reset_history: Optional[bool] = False
    channel: Optional[str] = "ui"


class ChatResponse(BaseModel):
    response: str
    history_length: int


class ReasonResponse(BaseModel):
    response: str
    sources: list[dict]
    tools_used: list[str]
    actions_taken: list[str]
    actions_proposed: list[str]
    provider_used: str
    model_used: str
    grounded: bool
    degraded: bool
    degraded_reason: str
    latency_ms: int | None = None
    audit_id: str


class QuickExpenseRequest(BaseModel):
    amount: float
    description: str
    category: str = "Other"
    account: str
    date: Optional[str] = None
    notes: str = ""


class QuickIncomeRequest(BaseModel):
    amount: float
    description: str
    account: str
    date: Optional[str] = None
    notes: str = ""


@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    global conversation_history
    if request.reset_history:
        conversation_history = []
    response, conversation_history = chat(
        request.message, conversation_history, channel=request.channel
    )
    return ChatResponse(response=response, history_length=len(conversation_history))


@app.post("/reason", response_model=ReasonResponse)
async def reason_endpoint(request: ChatRequest):
    result = reason(request.message, conversation_history=conversation_history, channel=request.channel)
    return ReasonResponse(**result.to_dict())


@app.post("/voice")
async def voice_endpoint(audio: UploadFile = File(...)):
    global conversation_history
    from voice.transcriber import transcribe_bytes

    audio_bytes = await audio.read()
    extension = audio.filename.split(".")[-1] if audio.filename else "wav"
    transcribed = transcribe_bytes(audio_bytes, extension)
    if not transcribed:
        raise HTTPException(status_code=400, detail="Could not transcribe audio")
    response, conversation_history = chat(transcribed, conversation_history, channel="voice")
    return {"transcription": transcribed, "response": response}


@app.post("/brief")
async def trigger_brief():
    from agents.brief import run_brief

    return {"brief": run_brief()}


@app.get("/history")
async def get_history():
    return get_recent_conversations(limit=50)


@app.get("/decisions")
async def get_all_decisions():
    return get_decisions(limit=100)


@app.get("/patterns")
async def get_patterns():
    return get_active_patterns()


@app.get("/vault")
async def get_vault():
    return get_vault_snapshot()


@app.post("/reindex")
async def reindex():
    from search.indexer import index_meridian_vault, index_decisions

    vault_result = index_meridian_vault()
    index_decisions()
    return {"vault": vault_result, "decisions": "indexed"}


@app.post("/triggers/run")
async def run_triggers():
    from core.triggers import run_all_triggers

    run_all_triggers()
    return {"status": "Triggers evaluated"}


@app.get("/pantheon/overview")
async def pantheon_overview():
    return get_overview_snapshot()


@app.get("/pantheon/subsystems")
async def pantheon_subsystems():
    overview = get_overview_snapshot()
    return overview["health"]


@app.get("/pantheon/blackbook")
async def pantheon_blackbook():
    return get_blackbook_snapshot()


@app.post("/pantheon/blackbook/expense")
async def pantheon_blackbook_expense(payload: QuickExpenseRequest):
    result = blackbook.add_expense(
        amount=payload.amount,
        description=payload.description,
        category=payload.category,
        account_name=payload.account,
        tx_date=payload.date,
        notes=payload.notes,
    )
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error", "Unable to add expense"))
    return get_blackbook_snapshot()


@app.post("/pantheon/blackbook/income")
async def pantheon_blackbook_income(payload: QuickIncomeRequest):
    result = blackbook.add_income(
        amount=payload.amount,
        description=payload.description,
        account_name=payload.account,
        tx_date=payload.date,
        notes=payload.notes,
    )
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error", "Unable to add income"))
    return get_blackbook_snapshot()


@app.get("/pantheon/maridian")
async def pantheon_maridian():
    return get_maridian_snapshot()


@app.post("/pantheon/maridian/run-cycle")
async def pantheon_maridian_run_cycle():
    result = maridian.run_cycle()
    if not result.get("success"):
        raise HTTPException(status_code=500, detail=result.get("error") or result.get("stderr") or "Cycle failed")
    return {
        "status": "ok",
        "result": result,
        "snapshot": get_maridian_snapshot(),
    }


@app.get("/pantheon/olympus")
async def pantheon_olympus():
    return get_olympus_snapshot()


@app.get("/pantheon/activity")
async def pantheon_activity():
    return get_activity_snapshot(limit=12)


@app.get("/pantheon/doctor")
async def pantheon_doctor():
    return get_doctor_snapshot()


@app.get("/agents")
async def get_agents():
    from agents.hub import list_agents

    return list_agents()


@app.post("/agents")
async def create_new_agent(payload: dict):
    from agents.hub import create_agent

    agent_id = create_agent(
        name=payload["name"],
        description=payload["description"],
        system_prompt=payload["system_prompt"],
        schedule_expr=payload.get("schedule", "daily at 09:00"),
        tools_allowed=payload.get("tools", []),
    )
    return {"agent_id": agent_id, "status": "created"}


@app.delete("/agents/{agent_id}")
async def retire_agent_endpoint(agent_id: int):
    from agents.hub import retire_agent

    retire_agent(agent_id)
    return {"status": "retired"}


@app.get("/health")
async def health():
    return {"status": "Apollo is running"}


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8001, reload=True)
