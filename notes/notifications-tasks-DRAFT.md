# Notifications tasks
There is a user_notifications table, with a corresponding SqlAlchemy model, and a full-featured API already. There is a 
notification bell icon with dropdown in the navabar. I believe that notifications might be wired up correctly with 
celery. I believe that the generations page, when an image is completed, is supposed to send a notification to the user. 
I believe that this may be the only notification currently.

But there are more tasks.

### 1. Frontend - Notifications Page
- [ ] Create `frontend/src/pages/notifications/NotificationsPage.tsx`:
  - [ ] Display paginated list of all notifications
  - [ ] Show notification type icon, title, message, timestamp
  - [ ] Highlight unread notifications
  - [ ] Mark as read on click
  - [ ] Add "Mark all as read" button
  - [ ] Add delete functionality
  - [ ] Filter by notification type
  - [ ] Sort by date
- [ ] Add route for notifications page (if doesn't exist)

### 2 Frontend - Toast/Banner Notifications
- [ ] Implement toast notification system:
  - [ ] Show toast when generation job completes (if notifications enabled)
  - [ ] Show toast when job fails (if notifications enabled)
  - [ ] Make toasts closeable
  - [ ] Auto-dismiss after 5-10 seconds
- [ ] Or implement banner notification at top of page (alternative to toast)

### 3. Frontend - User Settings Integration
- [ ] Settings (part 1): Update user settings page to include notification preferences:
  - [ ] Add toggle for "Enable toast notifications" (default: off)
  - [ ] Save preferences to backend
- [ ] Settings (part 2): Create settings navigation sidebar (right side of settings pages):
  - [ ] "Account Settings" link
  - [ ] "Notifications" link
  - [ ] Accessible from profile icon or cog icon

### 4. Frontend - Admin control panel updates
DESCRIBE

- [ ] In the "Admin Control Panel" page, add a "Notifications" tab if it doesn't exist. Otherwise, if it already exists 
  or once it exists, add a.... TODO  

TODO: Include notes about: 
- title, notification, type
- type should be valid. should have enum somewhere. i think like info, warning, error
 
### 5. Backend? - Admin messages
- [ ] I think it might be the case that the frontend works... but if not, TODO
- [ ] Test: If any backend work was necessary, add testing.

### 6. Backend - Database seeding
- [ ] Add a function that... TODO: message
- [ ] Set up the seed script so that ...TODO

### 7. Frontend Testing
- [ ] Unit tests for notification service
- [ ] Component tests for bell icon and dropdown
- [ ] Component tests for notifications page
- [ ] E2E test for complete notification flow
