# Story 8: Friendship System

**Phase:** 2 - Social Features  
**Points:** 3 (3 days)  
**Priority:** 🟡 MEDIUM  
**Dependencies:** [Phase 1 Complete](../phase-1/)

---

## 📖 Description

Implement friendship system: send requests, accept/reject, list friends, search users, và remove friends.

---

## 🎯 Goals

- [ ] Users can send friend requests
- [ ] Users can accept/reject requests
- [ ] Friends list API working
- [ ] User search implemented
- [ ] Friend removal working

---

## ✅ Acceptance Criteria

### 1. Send Friend Request
- [ ] `POST /friends/request` - Send request
- [ ] Validates addressee exists
- [ ] Prevents duplicate requests
- [ ] Cannot send to self
- [ ] Creates notification

### 2. Respond to Request
- [ ] `POST /friends/{id}/respond` - Accept/reject/block
- [ ] Updates friendship status
- [ ] Notifies requester on accept
- [ ] Only addressee can respond

### 3. List Friends
- [ ] `GET /friends` - List accepted friends
- [ ] Filter by status (accepted, pending)
- [ ] Returns friend profiles with stats

### 4. Search Users
- [ ] `GET /users/search` - Full-text search
- [ ] By display name or email
- [ ] Shows friendship status
- [ ] Max 20 results

### 5. Remove Friend
- [ ] `DELETE /friends/{user_id}` - Remove friend
- [ ] Deletes friendship record
- [ ] Either party can remove

---

## 📦 Implementation Files

```
app/api/v1/friends.py
app/schemas/friendship.py
tests/test_friends.py
```

---

## 🧪 Key Tests

- Send request success
- Duplicate request rejected
- Accept request success
- Search by name/email
- Remove friend success

---

**Next:** [Story 9: Notification System](./story-9-notifications.md)
