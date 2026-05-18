from pydantic import BaseModel


class StartAnalysisRequest(BaseModel):
    patientId: str
    signal: str