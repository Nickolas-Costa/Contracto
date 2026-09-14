"""DTOs limitados e sem caminhos de filesystem fornecidos pelo cliente."""
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, StringConstraints

Id = Annotated[str, StringConstraints(pattern=r"^[a-f0-9]{32}$")]
Text = Annotated[str, StringConstraints(max_length=4000)]


class Model(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, allow_inf_nan=False)


class ParticipantInput(Model):
    nome_completo: Annotated[str, StringConstraints(min_length=1, max_length=200)]
    cpf: Annotated[str, StringConstraints(min_length=11, max_length=18)]
    endereco: Text = ""
    data_assinatura: Annotated[str, StringConstraints(max_length=10)] = ""
    local_assinatura: Annotated[str, StringConstraints(max_length=200)] = ""
    campos_dinamicos: dict[Annotated[str, StringConstraints(max_length=100)], Text | bool | int | float] = Field(default_factory=dict, max_length=200)


class ComposeInput(Model):
    profile_ids: list[Id] = Field(min_length=1, max_length=20)


class EmptyInput(Model):
    pass


class PreviewInput(ComposeInput):
    participants: list[ParticipantInput] = Field(min_length=1, max_length=4)


class GenerateInput(PreviewInput):
    request_id: Id | None = None
    output_id: Id


class Attachment(Model):
    file_id: Id
    document_type: Annotated[str, StringConstraints(pattern=r"^[A-Za-z0-9_-]{1,50}$")]


class ProcessInput(Model):
    request_id: Id | None = None
    participants: list[ParticipantInput] = Field(min_length=1, max_length=4)
    output_id: Id
    file_ids: list[Id] = Field(default_factory=list, max_length=100)
    attachments: list[Attachment] = Field(default_factory=list, max_length=100)
    format: Literal["PDF", "PDF/A-2b"] = "PDF"


class Error(Model):
    code: str
    message: str


class JobState(Model):
    job_id: Id
    status: Literal["queued", "running", "cancelling", "cancelled", "completed", "failed"]
    completed: int = 0
    total: int = 0
    file_ids: list[Id] = Field(default_factory=list)
    error: Error | None = None
