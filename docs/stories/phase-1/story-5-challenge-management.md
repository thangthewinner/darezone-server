# Story 5: Challenge Management

**Phase:** 1 - Core Backend  
**Points:** 5 (5 days)  
**Priority:** 🔥 CRITICAL  
**Dependencies:** [Story 4: User Management](./story-4-user-management.md)

---

## 📖 Description

Implement full CRUD cho challenges: create, list, get, update, delete, join via invite code, leave, và member management.

---

## 🎯 Goals

- [ ] Users can create challenges with habits
- [ ] Invite code generation working
- [ ] Users can join via invite code
- [ ] Members can leave challenges
- [ ] Challenge stats updated correctly
- [ ] RLS enforced (members only access)

---

## ✅ Acceptance Criteria

### 1. Challenge Creation API
- [ ] `POST /challenges` - Create challenge
- [ ] Validates habit_ids exist
- [ ] Generates unique 6-char invite code
- [ ] Auto-adds creator as member with 'creator' role
- [ ] Sets initial hitch_count = 2
- [ ] Max 4 habits per challenge enforced

### 2. Challenge List API
- [ ] `GET /challenges` - List my challenges
- [ ] Filter by status (active, completed, etc.)
- [ ] Pagination support (page, limit)
- [ ] Sorted by created_at DESC

### 3. Challenge Detail API
- [ ] `GET /challenges/{id}` - Get full challenge
- [ ] Includes members list with stats
- [ ] Includes habits list
- [ ] Shows my membership info
- [ ] RLS: Only members can view

### 4. Join Challenge API
- [ ] `POST /challenges/join` - Join via invite code
- [ ] Validates invite code exists
- [ ] Checks max_members limit
- [ ] Prevents duplicate membership
- [ ] Creates notification for creator

### 5. Leave Challenge API
- [ ] `POST /challenges/{id}/leave` - Leave challenge
- [ ] Updates status to 'left'
- [ ] Preserves stats (streak, points) for history
- [ ] Cannot leave if creator (must delete instead)
- [ ] Notifies other members

### 6. Challenge Update API
- [ ] `PATCH /challenges/{id}` - Update challenge
- [ ] Only creator/admin can update
- [ ] Can change name, description, status

### 7. Members API
- [ ] `GET /challenges/{id}/members` - List members
- [ ] Shows role, status, stats
- [ ] DELETE `/challenges/{id}/members/{user_id}` - Kick member (B2B)

### 8. Progress API
- [ ] `GET /challenges/{id}/progress` - Today's progress
- [ ] Shows which habits each member completed
- [ ] Used for "Who's checked in?" UI

---

## 🛠️ Technical Implementation

### Challenge Create Flow

```
User submits:
  - name, description
  - start_date, end_date
  - habit_ids (1-4)
  - type (individual/group)
      ↓
Backend validates:
  - Habits exist
  - Date range valid (end > start, duration <= 365)
  - Max 4 habits
      ↓
Create challenge:
  - Generate invite_code = random 6 chars
  - Set status = 'pending'
  - Set created_by = current_user.id
      ↓
Auto-create member:
  - role = 'creator'
  - status = 'active'
  - hitch_count = 2
      ↓
Insert challenge_habits for each habit
      ↓
Return challenge with invite_code
```

### Join Flow

```
User submits invite_code: "ABC123"
      ↓
Find challenge by invite_code
      ↓
Validate:
  - Challenge exists
  - Not already a member
  - member_count < max_members
      ↓
Create membership:
  - role = 'member'
  - status = 'active'
  - hitch_count = 2
      ↓
Increment challenge.member_count
      ↓
Notify creator: "User X joined your challenge"
      ↓
Return challenge details
```

### Key Code Snippets

```python
# app/api/v1/challenges.py

@router.post("/challenges", response_model=Challenge, status_code=201)
async def create_challenge(
    challenge: ChallengeCreate,
    current_user: Dict = Depends(get_current_active_user),
    supabase: Client = Depends(get_supabase_client)
):
    """Create new challenge"""
    
    # Validate habits
    habits_response = supabase.table('habits')\
        .select('id')\
        .in_('id', challenge.habit_ids)\
        .execute()
    
    if len(habits_response.data) != len(challenge.habit_ids):
        raise HTTPException(400, "Some habit IDs not found")
    
    # Generate invite code
    invite_code = generate_invite_code()
    
    # Create challenge
    challenge_data = {
        "name": challenge.name,
        "description": challenge.description,
        "type": challenge.type,
        "start_date": str(challenge.start_date),
        "end_date": str(challenge.end_date),
        "invite_code": invite_code,
        "created_by": current_user["id"],
        "checkin_type": challenge.checkin_type,
        "max_members": challenge.max_members,
    }
    
    challenge_response = supabase.table('challenges')\
        .insert(challenge_data)\
        .execute()
    
    challenge_id = challenge_response.data[0]["id"]
    
    # Add habits
    for idx, habit_id in enumerate(challenge.habit_ids):
        supabase.table('challenge_habits').insert({
            "challenge_id": challenge_id,
            "habit_id": habit_id,
            "display_order": idx
        }).execute()
    
    # Add creator as member
    supabase.table('challenge_members').insert({
        "challenge_id": challenge_id,
        "user_id": current_user["id"],
        "role": "creator",
        "status": "active",
        "hitch_count": 2
    }).execute()
    
    return challenge_response.data[0]


@router.post("/challenges/join", response_model=Challenge)
async def join_challenge(
    request: JoinChallengeRequest,
    current_user: Dict = Depends(get_current_active_user),
    supabase: Client = Depends(get_supabase_client)
):
    """Join challenge via invite code"""
    
    # Find challenge
    challenge_response = supabase.table('challenges')\
        .select('*')\
        .eq('invite_code', request.invite_code)\
        .single()\
        .execute()
    
    if not challenge_response.data:
        raise HTTPException(404, "Invalid invite code")
    
    challenge = challenge_response.data
    
    # Check already member
    existing = supabase.table('challenge_members')\
        .select('id')\
        .eq('challenge_id', challenge['id'])\
        .eq('user_id', current_user['id'])\
        .execute()
    
    if existing.data:
        raise HTTPException(400, "Already a member")
    
    # Check max members
    if challenge['member_count'] >= challenge['max_members']:
        raise HTTPException(400, "Challenge is full")
    
    # Add member
    supabase.table('challenge_members').insert({
        "challenge_id": challenge['id'],
        "user_id": current_user['id'],
        "role": "member",
        "status": "active",
        "hitch_count": 2
    }).execute()
    
    # Increment count
    supabase.table('challenges')\
        .update({"member_count": challenge['member_count'] + 1})\
        .eq('id', challenge['id'])\
        .execute()
    
    # Notify creator
    await create_notification(
        supabase,
        user_id=challenge['created_by'],
        type='member_joined',
        title='New Member!',
        body=f"{current_user['profile']['display_name']} joined your challenge"
    )
    
    return challenge


def generate_invite_code() -> str:
    """Generate 6-char invite code"""
    import random
    import string
    chars = string.ascii_uppercase + string.digits
    chars = chars.replace('0', '').replace('O', '').replace('I', '').replace('1')
    return ''.join(random.choices(chars, k=6))
```

---

## 📦 Files to Create

```
app/
├── api/v1/
│   └── challenges.py            # 🆕 Challenge endpoints
├── schemas/
│   └── challenge.py             # 🆕 Challenge DTOs
├── services/
│   └── challenge_service.py     # 🆕 Business logic
└── repositories/
    └── challenge_repository.py  # 🆕 Data access
tests/
└── test_challenges.py           # 🆕 Challenge tests
```

---

## 🧪 Testing Checklist

```python
# Test scenarios

def test_create_challenge_success():
    """Create challenge with valid data"""
    # Should return 201 with invite_code

def test_create_challenge_invalid_habits():
    """Create with non-existent habit IDs"""
    # Should return 400

def test_create_challenge_too_many_habits():
    """Create with 5+ habits"""
    # Should return 400

def test_join_challenge_success():
    """Join via valid invite code"""
    # Should add member, increment count

def test_join_challenge_invalid_code():
    """Join with wrong code"""
    # Should return 404

def test_join_challenge_already_member():
    """Join challenge twice"""
    # Should return 400

def test_leave_challenge_success():
    """Member leaves challenge"""
    # Should set status = 'left'

def test_leave_challenge_as_creator():
    """Creator tries to leave"""
    # Should return 400 (must delete instead)

def test_list_challenges_pagination():
    """List with page=2, limit=10"""
    # Should return correct slice

def test_get_challenge_unauthorized():
    """Non-member tries to view challenge"""
    # Should return 403 (RLS blocks)
```

---

## ✅ Definition of Done

- [ ] All CRUD endpoints working
- [ ] Invite code generation unique
- [ ] Join flow complete with validations
- [ ] Leave flow preserves stats
- [ ] RLS enforced on all operations
- [ ] Member count updates correctly
- [ ] Notifications sent
- [ ] All tests pass (>90% coverage)
- [ ] Swagger docs complete
- [ ] Code reviewed

---

**Previous:** [Story 4: User Management](./story-4-user-management.md)  
**Next:** [Story 6: Check-in System](./story-6-checkin-system.md)
