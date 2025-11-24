# Story 15: Analytics & Reporting

**Phase:** 3 - B2B & Advanced  
**Points:** 3 (3 days)  
**Priority:** 🟢 LOW (B2B Optional)  
**Dependencies:** [Story 14: Programs](./story-14-programs.md)

---

## 📖 Description

Implement analytics dashboard cho B2B orgs: participation rates, completion trends, top performers.

---

## 🎯 Goals

- [ ] Org-level analytics dashboard
- [ ] Date range filtering
- [ ] Export to CSV
- [ ] Visual chart data

---

## ✅ Acceptance Criteria

### 1. Analytics Endpoints
- [ ] `GET /admin/analytics/overview` - High-level metrics
- [ ] `GET /admin/analytics/participation` - Daily participation
- [ ] `GET /admin/analytics/completion` - Completion rates
- [ ] `GET /admin/analytics/leaderboard` - Top performers

### 2. Metrics Calculated
- [ ] Total members, active members
- [ ] Average completion rate
- [ ] Participation trend (7/30 days)
- [ ] Top habits by engagement

### 3. Data Export
- [ ] Export to CSV
- [ ] Date range selection
- [ ] Member-level details

---

## 🛠️ Implementation

```python
# app/api/v1/analytics.py

@router.get("/admin/analytics/overview")
async def get_analytics_overview(
    start_date: date,
    end_date: date,
    current_user = Depends(get_b2b_admin),
    supabase: Client = Depends(get_supabase_client)
):
    """Get organization analytics overview"""
    # Calculate metrics
    # Return dashboard data
    pass
```

---

## ✅ Definition of Done

- [ ] Analytics endpoints working
- [ ] Metrics accurate
- [ ] CSV export functional
- [ ] Tests pass

---

**Next:** [Story 16: Performance](./story-16-performance.md)
