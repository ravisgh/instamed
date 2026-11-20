from typing import Any

from pydantic import BaseModel, model_validator


class UpdateModel(BaseModel):
    """Base for PATCH bodies: every field optional, but at least one must be given."""

    @model_validator(mode="after")
    def _require_at_least_one_field(self):
        if not self.changes():
            raise ValueError("provide at least one field to update")
        return self

    def changes(self) -> dict[str, Any]:
        """Only the fields the client actually sent (nulls ignored), JSON-ready."""
        return self.model_dump(mode="json", exclude_unset=True, exclude_none=True)
