from typing import Optional

from pydantic import BaseModel


class StartAnalysisRequest(BaseModel):
    patientId: str
    signal: str
    language: Optional[str] = "zh"
