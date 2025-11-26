from fastapi import APIRouter, Depends, HTTPException
from supabase import Client
from app.core.dependencies import get_supabase_client
from app.core.security import get_current_active_user
from app.schemas.hitch import HitchRequest, HitchResponse

router = APIRouter()


@router.post("", response_model=HitchResponse)
async def send_hitch(
    request: HitchRequest,
    current_user=Depends(get_current_active_user),
    supabase: Client = Depends(get_supabase_client),
):
    """
    Send hitch reminder to challenge members
    
    **Hitch System:**
    - Each member gets 2 hitches per challenge (default)
    - Use hitches to remind friends who haven't checked in
    - Rate limit: 1 hitch per habit per target per day
    - Sends notification to reminded users
    
    **Process:**
    1. Validates sender is active member with hitches remaining
    2. Validates all targets are active members
    3. Creates hitch_log entries (skips if duplicate today)
    4. Sends notifications to targets
    5. Decrements sender's hitch_count
    
    **Returns:**
    - `hitches_sent`: Number of reminders actually sent
    - `remaining_hitches`: Hitches left for sender
    
    **Errors:**
    - 400: No hitches remaining
    - 400: No valid targets (all already received hitch today)
    - 403: Sender not a member of challenge
    - 404: Challenge or habit not found
    """
    try:
        # Call RPC function for atomic operation
        result = supabase.rpc(
            "send_hitch_reminder",
            {
                "p_challenge_id": request.challenge_id,
                "p_habit_id": request.habit_id,
                "p_sender_id": current_user["id"],
                "p_target_ids": request.target_user_ids,
            },
        ).execute()

        # Check if RPC returned data
        if not result.data or len(result.data) == 0:
            raise HTTPException(
                status_code=500,
                detail="Failed to send hitch reminder",
            )

        # Extract results from RPC
        data = result.data[0]
        hitches_sent = data.get("hitches_sent", 0)
        remaining_hitches = data.get("remaining_hitches", 0)

        return HitchResponse(
            success=True,
            hitches_sent=hitches_sent,
            remaining_hitches=remaining_hitches,
            message=f"Sent {hitches_sent} reminder{'s' if hitches_sent != 1 else ''}. {remaining_hitches} hitch{'es' if remaining_hitches != 1 else ''} remaining.",
        )

    except Exception as e:
        error_msg = str(e).lower()

        # Parse specific error messages from RPC function
        if "no hitches remaining" in error_msg:
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "No hitches remaining",
                    "message": "You have used all your hitches for this challenge",
                },
            )
        elif "not a member" in error_msg or "not an active member" in error_msg:
            raise HTTPException(
                status_code=403,
                detail={
                    "error": "Not a member",
                    "message": "You must be an active member of this challenge to send hitch reminders",
                },
            )
        elif "no valid targets" in error_msg or "already received" in error_msg:
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "No valid targets",
                    "message": "All targets have already received a hitch reminder today for this habit",
                },
            )
        elif "habit not found" in error_msg:
            raise HTTPException(
                status_code=404,
                detail={
                    "error": "Habit not found",
                    "message": "The specified habit does not exist",
                },
            )
        else:
            # Generic error
            raise HTTPException(
                status_code=500,
                detail={
                    "error": "Failed to send hitch",
                    "message": str(e),
                },
            )
