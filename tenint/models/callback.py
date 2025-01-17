from pydantic import BaseModel


class CallbackDataTypeCounts(BaseModel):
    sent: int = 0
    modified: int = 0
    failed: int = 0


class CallbackCounters(BaseModel):
    assets: CallbackDataTypeCounts = CallbackDataTypeCounts()
    findings: CallbackDataTypeCounts = CallbackDataTypeCounts()


class CallbackResponse(BaseModel):
    exit_code: int
    counts: CallbackCounters = CallbackCounters()
