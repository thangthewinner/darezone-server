# DareZone API Documentation

**Version:** 1.0.0  
**Base URL:** `http://localhost:8000/api/v1`  
**Authentication:** Bearer Token (JWT)

## Quick Links

- **Interactive API Docs:** [http://localhost:8000/docs](http://localhost:8000/docs) (Swagger UI)
- **Alternative Docs:** [http://localhost:8000/redoc](http://localhost:8000/redoc) (ReDoc)
- **Health Check:** [http://localhost:8000/health](http://localhost:8000/health)

## Authentication

All API endpoints (except health check) require authentication using JWT tokens from Supabase Auth.

### Headers

```
Authorization: Bearer <your_jwt_token>
Content-Type: application/json
```

## Core Endpoints

### Authentication
- `POST /auth/verify` - Verify JWT token
- `GET /auth/me` - Get current user profile
- `POST /auth/logout` - Logout user

### Users
- `GET /users/me` - Get my profile
- `PATCH /users/me` - Update my profile
- `GET /users/{user_id}` - Get user profile
- `GET /users/search` - Search users

### Challenges
- `POST /challenges` - Create challenge
- `GET /challenges` - List my challenges
- `GET /challenges/{id}` - Get challenge details
- `POST /challenges/join` - Join challenge via invite code
- `PATCH /challenges/{id}` - Update challenge
- `POST /challenges/{id}/leave` - Leave challenge
- `GET /challenges/{id}/members` - Get challenge members
- `GET /challenges/{id}/progress` - Get today's progress

### Check-ins
- `POST /checkins` - Submit daily check-in
- `GET /checkins` - Get my check-ins
- `GET /checkins/today` - Get today's check-ins
- `GET /checkins/challenge/{id}` - Get challenge check-ins

### Friends
- `POST /friends/request` - Send friend request
- `GET /friends` - List my friends
- `GET /friends/requests` - List friend requests
- `POST /friends/{id}/accept` - Accept friend request
- `POST /friends/{id}/reject` - Reject friend request
- `DELETE /friends/{id}` - Remove friend

### Notifications
- `GET /notifications` - List my notifications
- `PATCH /notifications/{id}/read` - Mark as read
- `DELETE /notifications/{id}` - Delete notification

### Media
- `POST /media/upload` - Upload photo/video
- `GET /media/{id}` - Get media URL

### Hitch (Reminders)
- `POST /hitch` - Send hitch reminder
- `GET /hitch/received` - Get received hitches
- `GET /hitch/sent` - Get sent hitches

### Stats & History
- `GET /stats/me` - Get my statistics
- `GET /stats/challenge/{id}` - Get challenge statistics
- `GET /stats/leaderboard` - Get leaderboard

## Response Format

### Success Response
```json
{
  "id": "uuid",
  "name": "Challenge Name",
  "status": "active",
  ...
}
```

### Error Response
```json
{
  "detail": "Error message"
}
```

## Status Codes

- `200` - Success
- `201` - Created
- `400` - Bad Request
- `401` - Unauthorized
- `403` - Forbidden
- `404` - Not Found
- `422` - Validation Error
- `500` - Internal Server Error

## Data Models

### Challenge Types
- `individual` - Solo challenge
- `group` - Group challenge

### Challenge Status
- `pending` - Not started
- `active` - In progress
- `completed` - Successfully completed
- `failed` - Failed to complete
- `archived` - Archived

### Member Roles
- `creator` - Challenge creator
- `admin` - Co-admin
- `member` - Regular member

### Member Status
- `pending` - Invitation pending
- `active` - Active member
- `left` - Left the challenge
- `kicked` - Removed from challenge

## Examples

### Create a Challenge

```bash
curl -X POST http://localhost:8000/api/v1/challenges \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Morning Routine",
    "description": "Wake up early every day",
    "type": "group",
    "start_date": "2026-01-04",
    "end_date": "2026-01-31",
    "habit_ids": ["habit-uuid-1", "habit-uuid-2"],
    "max_members": 10,
    "is_public": false
  }'
```

### Submit Check-in

```bash
curl -X POST http://localhost:8000/api/v1/checkins \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "challenge_id": "challenge-uuid",
    "habit_id": "habit-uuid",
    "photo_url": "https://storage.url/photo.jpg",
    "caption": "Done for today!"
  }'
```

### Join Challenge

```bash
curl -X POST http://localhost:8000/api/v1/challenges/join \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "invite_code": "ABC123"
  }'
```

## Rate Limits

- Hitch reminders: 1 per habit per target per day
- API calls: No limit (production will have rate limiting)

## Notes

- All dates are in ISO 8601 format (`YYYY-MM-DD`)
- All timestamps are in ISO 8601 format with timezone
- UUIDs are used for all IDs
- Snake_case is used in database, camelCase in API responses (auto-transformed)

## Support

For detailed interactive documentation, visit [http://localhost:8000/docs](http://localhost:8000/docs)
