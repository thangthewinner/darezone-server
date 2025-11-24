# Story 13: B2B Organizations

**Phase:** 3 - B2B & Advanced  
**Points:** 3 (3 days)  
**Priority:** 🟢 LOW (Optional for MVP)  
**Dependencies:** [Phase 2 Complete](../phase-2/)

---

## 📖 Description

Implement B2B organizations system: create orgs, manage members, assign roles, và org-level settings.

---

## 🎯 Goals

- [ ] Orgs can be created by B2B admins
- [ ] Members can be added to orgs
- [ ] Org-level challenges supported
- [ ] Admin dashboard data available

---

## ✅ Acceptance Criteria

### 1. Organization CRUD
- [ ] `POST /admin/organizations` - Create org
- [ ] `GET /admin/organizations` - List my orgs
- [ ] `PATCH /admin/organizations/{id}` - Update org

### 2. Member Management
- [ ] `POST /admin/organizations/{id}/members` - Add member
- [ ] `GET /admin/organizations/{id}/members` - List members
- [ ] `DELETE /admin/organizations/{id}/members/{user_id}` - Remove member

### 3. Org Settings
- [ ] Max members enforcement
- [ ] Plan-based feature flags
- [ ] Org-scoped challenges

---

## 📦 Implementation Files

```
app/api/v1/admin.py
app/schemas/organization.py
tests/test_organizations.py
```

---

**Next:** [Story 14: Programs & Cohorts](./story-14-programs.md)
