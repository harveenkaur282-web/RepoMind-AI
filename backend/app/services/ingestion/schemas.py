from pydantic import BaseModel


class ProcessedFile(BaseModel):
    path: str
    content: str
