from pydantic import BaseModel, Field
from typing import Optional, Literal

from app.utils import generate_timestamp


class Model(BaseModel):
    id: str  # Model identifier, also used in the HuggingFace model hub
    created_at: int = Field(default_factory=generate_timestamp)
    status: Literal["training", "trained", "failed", "deleted"]  # Model status
    owned_by: Optional[str] = None  # Owner identifier: phospho or org_id
    task_type: Optional[str] = (
        None  # Task identifier, for won we only support "binary-classification"
    )
    context_window: Optional[int] = None  # Context window size of the model, in tokens


class ModelsResponse(BaseModel):
    models: list  # List of models objects
