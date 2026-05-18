from pydantic import BaseModel


class DoctorFeedbackRequest(BaseModel):
    feedback: str
    comment: str = ""