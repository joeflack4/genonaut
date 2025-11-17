# Bookmarks feature - data model
## Starting instructions
We want to add a feature where users can 'favorite' images, and organized those favorites into categories. We're calling 
this favoriting system 'bookmarks'. We're going to start by defining the data model in `schema.md`.

**Schema**:

_Table 1 - `bookmarks`_
Fields:
id (uuid, PK)
user_id (FK users.id)
content_id (FK content_items_all.id)
note (text)
pinned (bool, default false)
is_public (bool, default false)
created_at (timestamptz)
updated_at (timestamptz)
deleted_at (timestamptz, nullable) — soft delete
 
Indexes:
(user_id)
(content_id)
(is_public)
 
Constraints:
UNIQUE (user_id, content_id)

_Table 2 - `bookmark_categories`_
Fields:
id (uuid, PK)
user_id (FK users.id)
name (varchar(100))
description (text)
color_hex (varchar(7))
icon (varchar(64))
cover_content_id (FK content_items_all.id, nullable)
parent_id (FK self.id, ON DELETE SET NULL)
sort_index (int) - This is for when we allow user to manually sort the order in which categories appear on the bookmarks categories page
is_public (bool, default false)
share_token (uuid, nullable) — public/secret link
created_at (timestamptz)
updated_at (timestamptz)
 
Indexes:
(user_id)
(parent_id)
 
Constraints:
UNIQUE (user_id, name, parent_id) (optional)
 
RLS:
Enforce user_id match across FKs (via CHECK or trigger)
More discussed on this in section below: Details > RLS

_Table 3 - `bookmark_category_members`_
Fields:
bookmark_id (FK user_bookmarks.id, ON DELETE CASCADE)
category_id (FK user_bookmark_categories.id, ON DELETE CASCADE)
position (int) — order within category, for when the user wants to use manual sorting
added_at (timestamptz)
 
Constraints:
PRIMARY KEY (bookmark_id, category_id)


**Required prerequisite reading**:
Read and follow instructions laid out in these documents:
- .claude/commands/new-big-task.md
- notes/routines/iteration.md
- .claude/commands/migrations.md

**First tasks**:
- [x] 1. Read and understand the 'Required prerequisite reading'.
- [x] 2. Read and understand this document (bookmarks-data-model.md)
- [x] 3. Follow the instructions as laid out in `new-big-task.md` to begin this work.

**Implementation Plan**:
See `notes/bookmarks-implementation.md` for the detailed implementation plan with phased tasks.

## Details
### RLS (Row-level security)
Preface: Important considerations:
- SQL queries here are just examples. Remember, we're defining as much as possible (100%, if possible) in SqlAlchemy. We 
want to avoid manual sql in migrations or otherwise as much as possible.
- If anything here is unclear or contradictory, add questions for my review, and prompt me to answer them.

We want to guarantee parent/child (and membership) rows belong to the same user. That’s what “enforce
user_id match across FKs” means. It matters for self-references (categories → categories.parent_id) and join tables (
bookmark ↔ category). It’s not needed on user_bookmarks itself because it doesn’t self-reference; its FKs point to users
and global content_items_all.

Example SQL:
```sql
-- CATEGORIES: ensure parent is from same user
ALTER TABLE user_bookmark_categories
  ADD CONSTRAINT ubc_unique_id_user UNIQUE (id, user_id);

ALTER TABLE user_bookmark_categories
  ADD CONSTRAINT ubc_parent_same_user_fk
  FOREIGN KEY (parent_id, user_id)
  REFERENCES user_bookmark_categories (id, user_id)
  ON DELETE SET NULL;

-- MEMBERSHIP: ensure bookmark & category are from same user
ALTER TABLE user_bookmark_category_membership
  ADD COLUMN user_id uuid NOT NULL;

ALTER TABLE user_bookmarks
  ADD CONSTRAINT ub_unique_id_user UNIQUE (id, user_id);

ALTER TABLE user_bookmark_category_membership
  ADD CONSTRAINT ubcm_bookmark_same_user_fk
  FOREIGN KEY (bookmark_id, user_id)
  REFERENCES user_bookmarks (id, user_id)
  ON DELETE CASCADE;

ALTER TABLE user_bookmark_category_membership
  ADD CONSTRAINT ubcm_category_same_user_fk
  FOREIGN KEY (category_id, user_id)
  REFERENCES user_bookmark_categories (id, user_id)
  ON DELETE CASCADE;
```

Example SQL 2 - Here's a minimum “no-RLS” setup that’s safe:
```sql
-- Parents carry user_id and expose a composite key
ALTER TABLE user_bookmark_categories ADD CONSTRAINT ubc_uid UNIQUE (id, user_id);
ALTER TABLE user_bookmarks            ADD CONSTRAINT ub_uid  UNIQUE (id, user_id);

-- Membership row includes user_id and must match on BOTH sides
ALTER TABLE user_bookmark_category_membership
  ADD COLUMN user_id uuid NOT NULL,
  ADD CONSTRAINT fk_membership_bookmark_same_user
    FOREIGN KEY (bookmark_id, user_id)
    REFERENCES user_bookmarks (id, user_id)
    ON DELETE CASCADE,
  ADD CONSTRAINT fk_membership_category_same_user
    FOREIGN KEY (category_id, user_id)
    REFERENCES user_bookmark_categories (id, user_id)
    ON DELETE CASCADE;
```

Deriving & enforcing safe user ID operations via function:
```
-- 1) Parents expose (id, user_id)
ALTER TABLE user_bookmarks ADD CONSTRAINT ub_uid UNIQUE (id, user_id);
ALTER TABLE user_bookmark_categories ADD CONSTRAINT ubc_uid UNIQUE (id, user_id);

-- 2) Join table
ALTER TABLE user_bookmark_category_membership
  ADD COLUMN user_id uuid NOT NULL;

CREATE FUNCTION ubcm_set_user_id() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
  SELECT b.user_id INTO NEW.user_id
  FROM user_bookmarks b
  WHERE b.id = NEW.bookmark_id;
  RETURN NEW;
END$$;

CREATE TRIGGER ubcm_user_id_derive
BEFORE INSERT OR UPDATE OF bookmark_id ON user_bookmark_category_membership
FOR EACH ROW EXECUTE FUNCTION ubcm_set_user_id();

-- 3) Enforce same-user on both sides
ALTER TABLE user_bookmark_category_membership
  ADD CONSTRAINT fk_bm_same_user
    FOREIGN KEY (bookmark_id, user_id) REFERENCES user_bookmarks (id, user_id)
    ON DELETE CASCADE,
  ADD CONSTRAINT fk_cat_same_user
    FOREIGN KEY (category_id, user_id) REFERENCES user_bookmark_categories (id, user_id)
    ON DELETE CASCADE;
```

How it works (flow)
1. Client sends only bookmark_id and category_id (no user_id).
2. A BEFORE INSERT trigger looks up the bookmark’s owner and writes that into NEW.user_id.
3. Your composite FKs then ensure the category_id has the same user_id. If not, the insert fails.

Why it’s good
- Prevents “Alice puts Bob’s bookmark in Alice’s category” class bugs.
- Eliminates trusting client-supplied user_id.
- Plays nicely with or without RLS.

## Reports
