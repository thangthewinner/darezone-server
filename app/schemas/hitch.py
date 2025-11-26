from pydantic import BaseModel, Field
from typing import List


class HitchRequest(BaseModel):
    """Request to send hitch reminder to challenge members"""

    challenge_id: str = Field(..., description="UUID of the challenge")
    habit_id: str = Field(..., description="UUID of the habit to remind about")
    target_user_ids: List[str] = Field(
        ...,
        min_length=1,
        max_length=10,
        description="List of user IDs to send reminders to (1-10 users)",
    )

    class Config:
        json_schema_extra = {
            "example": {
                "challenge_id": "123e4567-e89b-12d3-a456-426614174000",
                "habit_id": "123e4567-e89b-12d3-a456-426614174001",
                "target_user_ids": [
                    "123e4567-e89b-12d3-a456-426614174002",
                    "123e4567-e89b-12d3-a456-426614174003",
                ],
            }
        }


class HitchResponse(BaseModel):
    """Response after sending hitch reminders"""

    success: bool = Field(..., description="Whether the operation succeeded")
    hitches_sent: int = Field(..., description="Number of reminders actually sent")
    remaining_hitches: int = Field(..., description="Hitches remaining for sender")
    message: str = Field(..., description="Human-readable result message")

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "hitches_sent": 2,
                "remaining_hitches": 1,
                "message": "Sent 2 reminders. 1 hitch remaining.",
            }
        }
