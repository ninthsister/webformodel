from typing import Optional

from pydantic import BaseModel


class DoctorFeedbackRequest(BaseModel):
    feedback: str
    comment: str = ""
    language: Optional[str] = "zh"
