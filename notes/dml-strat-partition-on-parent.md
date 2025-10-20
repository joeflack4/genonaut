# DML Strategy for Partitioned Parent Table (`content_items_all`)

## 🧩 Overview

Now that `content_items_all` is the **partitioned parent** of `content_items` and `content_items_auto`, the next step is
to migrate all **INSERT / UPDATE / DELETE** operations to target the **parent table** instead of the individual child tables.

This ensures that PostgreSQL’s built‑in **partition routing** works automatically, allowing one unified write path for
all content sources.

---

## ✅ Why Target the Parent Table

| Reason | Benefit |
|--------|----------|
| **Automatic routing** | Postgres routes rows to the correct partition (`source_type`) based on value |
| **Simpler app logic** | The app no longer needs to know which table (child) to use |
| **Consistent query path** | All reads/writes go through the same parent name (`content_items_all`) |
| **Future scalability** | Adding new partitions (e.g., by source or time) won’t require app changes |
| **Stable ORM mapping** | SQLAlchemy can map one model to the parent; Postgres handles routing |

---

## ⚙️ Behavior Details

### Inserts
- Must include a **valid `source_type`** (`'items'` or `'auto'`).
- If `source_type` is missing or invalid, Postgres raises:
  ```
  ERROR: no partition of relation "content_items_all" found for row
  ```
- Child tables still enforce their own constraints; rows land in correct partition automatically.

### Updates
- Work fine as long as you **don’t change `source_type`**.
- Postgres disallows updates that would move rows between partitions.
- `source_type` should remain `GENERATED ALWAYS` in child tables to prevent mistakes.

### Deletes
- Deletes via the parent are routed correctly and delete from the appropriate child partition automatically.

---

## ⚠️ Why Not Keep Writing to Children

| Problem | Explanation |
|----------|--------------|
| **Code duplication** | Every write path must choose the correct table manually |
| **Inconsistent queries** | Some joins and pagination will miss parent‑level optimizations |
| **Harder migrations** | Adding new partitions or splitting tables later requires code changes |
| **ORM complexity** | SQLAlchemy relationships, foreign keys, and sessions get messy |

---

## 🔨 Implementation Checklist

### Core DML Migration
- [ ] Update all **INSERT operations** to target `content_items_all`
- [ ] Update all **UPDATE operations** to target `content_items_all`
- [ ] Update all **DELETE operations** to target `content_items_all`
- [ ] Verify ORM model maps to parent (`__tablename__ = "content_items_all"`)
- [ ] Ensure `source_type` is always populated by business logic
- [ ] Add `CHECK` or `ENUM` constraint validation for allowed `source_type` values

### Testing
- [ ] Unit test: `INSERT` into parent routes to correct partition
- [ ] Unit test: `UPDATE` via parent modifies correct row in child
- [ ] Unit test: `DELETE` via parent removes correct row from child
- [ ] Unit test: invalid `source_type` → raises partition routing error
- [ ] Integration test: FK relationships remain valid after parent DML

### Optional (for Confidence & Safety)
- [ ] Keep temporary child‑directed DML paths (flagged for deprecation)
- [ ] Log or audit the actual partition name after inserts (for debugging)
- [ ] Add migration smoke test to verify partition routing on startup
- [ ] Monitor new inserts via parent in demo DB before prod rollout

---

## 🧠 Example: SQLAlchemy Model Pattern

```python
class ContentItem(Base):
    __tablename__ = "content_items_all"
    __table_args__ = {"postgresql_partition_by": "LIST (source_type)"}

    id: Mapped[int] = mapped_column(primary_key=True)
    source_type: Mapped[str]
    title: Mapped[str]
    created_at: Mapped[datetime]
    updated_at: Mapped[datetime]
    # ... other shared fields
```

Your ORM will automatically handle inserts like:
```python
session.add(ContentItem(source_type="auto", title="New auto content"))
```

Postgres routes it to `content_items_auto` behind the scenes.

---

## 🧭 TL;DR

| Operation | Preferred Target | Notes |
|------------|------------------|-------|
| INSERT | **Parent (`content_items_all`)** | Must include `source_type` |
| UPDATE | **Parent** | Works fine; `source_type` must not change |
| DELETE | **Parent** | Safely routed |
| SELECT | **Parent** | Full unified view |

---

**Result:**  
You’ll have a single logical entry point for all DML operations — safer, simpler, and future‑proof for additional partitions.
