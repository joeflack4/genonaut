# Tag Query Test Data (Demo Database)

**Generated**: 2025-10-21
**Database**: genonaut_demo

## Tag Combinations and Expected Counts

### Test Case 1: Single Tag - 'anime'
- **Tag ID**: `dfbb88fc-3c31-468f-a2d7-99605206c985`
- **Expected Count**: 836,134 content items
- **Query**: Single tag filter

### Test Case 2: Single Tag - '4k'
- **Tag ID**: `eeed7442-6374-4e2a-b110-f97fcc89df78`
- **Expected Count**: 836,262 content items
- **Query**: Single tag filter

### Test Case 3: Two Tags - 'anime' + '4k'
- **Tag IDs**:
  - anime: `dfbb88fc-3c31-468f-a2d7-99605206c985`
  - 4k: `eeed7442-6374-4e2a-b110-f97fcc89df78`
- **Expected Count**: 742,257 content items
- **Query**: Both tags (AND condition)

### Test Case 4: Five Tags
- **Tags Selected** (most popular tags):
  - pastel: `94ea732c-067c-4552-8d84-9663ef00e43a` (972,601 items)
  - moody: `45a09394-4710-4380-8d56-b18b8af361a2` (972,190 items)
  - crayon: `3cfa3c68-dac7-4034-ad6c-ab6b7fe639fa` (871,522 items)
  - flat: `edb00348-4517-473c-bb5d-3b3f4ad89be5` (871,474 items)
  - minimalist-typography: `0f5f42ca-6d96-4e56-9896-f331c339c5c1` (871,404 items)
- **Expected Count**: TBD (needs computation)

### Test Case 5: Twenty Tags
- **Tags Selected** (top 20 from list above):
  - pastel: `94ea732c-067c-4552-8d84-9663ef00e43a`
  - moody: `45a09394-4710-4380-8d56-b18b8af361a2`
  - crayon: `3cfa3c68-dac7-4034-ad6c-ab6b7fe639fa`
  - flat: `edb00348-4517-473c-bb5d-3b3f4ad89be5`
  - minimalist-typography: `0f5f42ca-6d96-4e56-9896-f331c339c5c1`
  - soft-light: `98e9f2e8-0b69-4537-b417-bc208bd82c70`
  - hand-drawn: `be35c31c-58cb-4d31-bccc-f41f20b54cba`
  - vibrant: `9076888a-3939-4ad7-8763-47fe3276babf`
  - installation: `0e62209e-97ad-4ddb-86e0-2494d7a61e41`
  - cinematic: `0e283364-214b-42a1-82fe-42382ab2043a`
  - vector: `ab7b665f-4b93-4285-b79f-ebb765e7c139`
  - glossy: `bf2a93fd-79b6-4f84-b072-4e23d9195498`
  - symmetrical: `e7461eb7-b898-4641-ac39-9675ee7af6ab`
  - experimental: `2823e3cd-63fd-4797-bd59-041ef350f386`
  - tilt-shift: `47575f40-d6ec-4946-aabc-bdb8c4fdd09e`
  - gothic: `3d7303d3-9939-4002-9e1c-4b4c50473891`
  - action: `44f9e5df-9ace-46eb-a6f7-615b30935c24`
  - isometric: `069dfa87-481a-4ee2-963c-1d16023fbc17`
  - horror: `41330e77-f595-41a5-9327-e101b42d2141`
  - thumbnail: `158354e1-5671-4154-9aa1-1cf2c04fbf41`
- **Expected Count**: TBD (needs computation)

## Notes

- These counts are from the demo database as of 2025-10-21
- Tag filtering uses AND logic (content must have ALL specified tags)
- Counts include both content_items and content_items_auto tables
- Frontend pagination uses page_size=25 by default
