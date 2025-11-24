# Story 14: Programs & Cohorts

**Phase:** 3 - B2B & Advanced  
**Points:** 3 (3 days)  
**Priority:** 🟢 LOW (B2B Optional)  
**Dependencies:** [Story 13: Organizations](./story-13-organizations.md)

---

## 📖 Description

Implement B2B programs system: recurring challenge templates với period-based cycles.

---

## 🎯 Goals

- [ ] Org admins can create programs
- [ ] Programs define challenge templates
- [ ] Periodic cohorts generated automatically
- [ ] Member progress tracked per program

---

## ✅ Acceptance Criteria

### 1. Program CRUD
- [ ] `POST /admin/programs` - Create program
- [ ] `GET /admin/programs` - List org programs
- [ ] `PATCH /admin/programs/{id}` - Update program
- [ ] `DELETE /admin/programs/{id}` - Archive program

### 2. Program Configuration
- [ ] Define: period (week/month), difficulty
- [ ] Set: habits per cycle, checkin type
- [ ] Generate: invite codes automatically

### 3. Cohort Management
- [ ] Auto-create challenges per cycle
- [ ] Track completion rates per cohort
- [ ] Historical cohort data

---

## 🛠️ Implementation

```python
# app/api/v1/programs.py

@router.post("/admin/programs")
async def create_program(
    program: ProgramCreate,
    current_user = Depends(get_b2b_admin),
    supabase: Client = Depends(get_supabase_client)
):
    """Create B2B program"""
    # Validate org membership
    # Create program
    # Setup automatic cohort generation
    pass

@router.get("/admin/programs")
async def list_programs(
    current_user = Depends(get_b2b_admin),
    supabase: Client = Depends(get_supabase_client)
):
    """List organization programs"""
    pass
```

---

## 📦 Files

```
app/api/v1/programs.py
app/schemas/program.py
tests/test_programs.py
```

---

## ✅ Definition of Done

- [ ] Program CRUD working
- [ ] Cohort auto-generation
- [ ] Progress tracking
- [ ] Tests pass

---

**Next:** [Story 15: Analytics](./story-15-analytics.md)
