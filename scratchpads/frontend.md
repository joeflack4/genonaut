# Frontend MVP spec

This document outlines the frontend development approach for Genonaut, including recommended technologies, architecture,
and integration with the FastAPI backend.

## Introduciton
We would like to implement a frontend for our app: genonaut. Right now we have a folder called genonaut, which is 
actually for backend code (Python, SQL, etc). I'd like to put the frontend in its own sibling folder; call it 
`frontend`.

Follow an architecture that follows the outline of this document. But, try to avoid upgrading to anything too advanced 
beyond this, as my dev team does not have advanced React / JavaScript developers, so we'd like to start with something 
that requires more intermediate level ReactJS ability to maintain.

For testing: Do TDD.

The backend API is well documented. See: docs/api.md. Also, Swagger / OpenAPI docs are running on localhost:8000/docs

What do I want the app to do?
This is a sort of recommender system for generative AI. In the future, I'm thinking about various modalities, but right 
now we are going to stick to image generation. We should have some basic common pages, such as login, sign up, and 
user/app settings. There is no authentication right now. So you can just treat it as if the user is already logged in, 
and their name can just be "Admin".

## Current Status

**🚧 Frontend Development Planned**

The backend API is complete and ready for frontend integration

## Technology Recommendations

### Primary Framework

**React + TypeScript**
- **Libraries:** React Query (API integration), Material-UI

### Development Stack

**Build Tools:**
- **NPM** - Package manager
- **Vite** - Fast build tool with excellent TypeScript support
- **ESLint + Prettier** - Code quality and formatting
- **Vitest** - Unit testing framework
- **PlayWright** - End-to-end testing framework. 
  - Pair with @playwright/test runner (already included in Playwright).

**API Integration:**
- **Axios or Fetch** - HTTP client for API requests
- **React Query / TanStack Query** - Data fetching and caching
- **OpenAPI Generator** - Auto-generate TypeScript types from API schema

**Styling:**
- **Component Library** - Material-UI

**State Management:**
- **React Context + useReducer** (for React)

## Architecture Overview

### Application Structure

```
docs/frontend/               # Frontend documentation
frontend/
├── src/
│   ├── components/          # Reusable UI components
│   │   ├── common/          # Generic components (Button, Input, etc.)
│   │   ├── layout/          # Layout components (Header, Sidebar, etc.)
│   │   └── domain/          # Domain-specific components
│   ├── pages/               # Page components/views
│   │   ├── users/           # User management pages
│   │   ├── content/         # Content management pages
│   │   ├── recommendations/ # Recommendation pages
│   │   └── dashboard/       # Dashboard and analytics
│   ├── hooks/               # Custom hooks (React) or composables (Vue)
│   ├── services/            # API service layer
│   ├── types/               # TypeScript type definitions
│   ├── utils/               # Utility functions
│   ├── stores/              # State management
│   └── assets/              # Static assets
├── public/                  # Public assets
└── tests/                   # Test files
```

### API Integration Layer

**Service Layer Pattern:**
```typescript
// services/api.ts
export class ApiClient {
  private baseURL = process.env.VITE_API_BASE_URL || 'http://localhost:8000';
  
  async get<T>(endpoint: string): Promise<T> {
    const response = await fetch(`${this.baseURL}${endpoint}`);
    return response.json();
  }
  
  async post<T>(endpoint: string, data: any): Promise<T> {
    const response = await fetch(`${this.baseURL}${endpoint}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    });
    return response.json();
  }
}

// services/userService.ts
export class UserService {
  constructor(private api: ApiClient) {}
  
  async getUser(id: number): Promise<User> {
    return this.api.get<User>(`/api/v1/users/${id}`);
  }
  
  async createUser(userData: UserCreateRequest): Promise<User> {
    return this.api.post<User>('/api/v1/users', userData);
  }
}
```

**Type Safety with OpenAPI:**
```bash
# Generate TypeScript types from API
npx openapi-typescript http://localhost:8000/openapi.json --output src/types/api.ts
```

## Core Features to Implement

### MVP Feature Set

**1. User Management Interface**
Overview:
- User registration and profile management
- User preferences configuration

This will be its own section with 1+ pages.

**2. Content Browser**
Right now the only content will be images. And there is metadata about those images.

Overview:
- Content listing with pagination and filtering
- Content detail views
- Content search functionality

This will be its own section with 1+ pages.

This app is high throughput. A typical user will likely have several thousand images of their own that they have used AI
to generate, and after doing so, they will come here to browse the results, rate, and tag them. They should be able to 
see the images as well as their metadata. They should be able to update certain metadata, such as the rating 
(quality_score in the db), tags, title, and is_private status. Obviously some certain fields and operations will require
user ownership in order for the user to make changes. For example, they won't be able to change the title of images 
created by another user, or the average rating shown for the item, or is_private status or the public tags for such 
items, but they can add their own personal tags and their own rating to an item that is not owned by them (I still need
to implement that on the backend). If they have ownership of an item, they can do all these changes, including delete
the item. The user should also be able to do filtering: tags (multiple select), rating (1 - 10) (the backend currently
has this as as a 0 to 1 scale, but that will change). And, the user should also be able to filter based searching for
prompts that match a text query. There will be a text box for that. Then, there will be some toggles: "match on
inclusion of any word", "match on inclusion of all words", "match on inclusion of only quoted words", "match on general
similarity". This should be a dropdown menu, with "match on general similarity" being the default.

Ater any filters are aplied, images can be sorted by date or popularity (rating).

**3. Recommendation Display**
- Personalized recommendation feed
- Recommendation explanation/reasoning
- Recommendation feedback collection

This will be a subsection of the "Content browser" section. The user should be able to see content that are personalized
recommendations vs content that is not.

The overall content browser should let the user see content of the following kinds of major categories:
- Global: Not recommended; just browsing by global catelog, which can further be filtered by tags.
- Recommended based on solid user preferences.
- Recommended based on exploring the users preference space.
- Recommended based on preferences of similar users.
- Recommended based on exploring the preference space f similar users.

**4. Generation**
This will be its own section with 1+ pages.

Later, this section will have lots of options, but for now, it will not have a lot. There will be a "Generate" button 
(green). When it is activated, there should be some status UI saying "generating". If generating is active, then the 
normally green "generate" button should instead be red and say "Stop". The page should have an integer input field for 
"batch size". The default should be 200, and max should be 1,000,000. Minimum should be 1. There should be a section 
called "Exploration options", for which there will be the following toggles: "Novel (based on my preferences)", "Novel 
(based on users like me)", "Novel (popular preferences)", "Stuff I'll probably like (based on my preferences)", "Stuff 
I'll probably like (based on users like me)", and ""Stuff I'll probably like (popular preferences)". Actually, I guess 
these labels are kind of redundant, so perhaps you can make this a table of checkboxes, with "Novel" and "Stuff I'll 
probably like" as row labels, and "Based on my preferences", "Based on users like me", and "Popular preferences" as the 
column headers.

**5. Interaction Tracking**
- Automatic interaction tracking (views, clicks)
- Rating and feedback components
- User interaction history

Unsure where to put these parts in the app; just know we want them.

**6. System Dashboard**
Overview:
- Global statistics visualization
- System health monitoring
- Basic analytics charts

This will be its own section with 1+ pages.

### User Interface Pages

**Authentication & User Management:**
- `/login` - User login (future)
- `/register` - User registration
- `/profile` - User profile management
- `/profile/preferences` - User preferences
- `/users` - User directory/search

**Content Management:**
- `/` - Home page with featured content
- `/content` - Content browser with filters
- `/content/:id` - Content detail view
- `/content/create` - Content creation form
- `/content/edit/:id` - Content editing
- `/search` - Advanced content search

**Recommendations:**
- `/recommendations` - Personal recommendation feed
- `/recommendations/history` - Recommendation history
- `/recommendations/settings` - Recommendation preferences

**Dashboard & Analytics:**
- `/dashboard` - Personal dashboard
- `/analytics` - System analytics (admin)
- `/stats` - Global statistics

**Generation**
- `/generation` – Create a new generation job (enter prompt + parameters).
- `/generation/:id` – View details of a specific generation job.
- `/generation/:id/edit` – Update a pending job’s parameters.
- `/generation/:id/status` – Monitor or update the job’s status.
- `/generation/:id/result` – View or set the generated result content.
- `/generation/history` – Browse past generation jobs with filters (by status, type, or user).
- `/generation/pending` – View all pending jobs (queue).
- `/generation/running` – View currently running jobs.
- `/generation/completed` – View completed jobs (last 30 days by default).
- `/generation/failed` – View failed jobs (last 7 days by default).
- `/generation/stats` – Overview of generation job statistics (global or per-user).
- `/generation/queue` – Queue monitoring: see stats (pending, running) and process queue manually (admin).

## Component Design System

### Base Components

**Form Components:**
```typescript
// Button component with variants
interface ButtonProps {
  variant: 'primary' | 'secondary' | 'danger';
  size: 'sm' | 'md' | 'lg';
  loading?: boolean;
  disabled?: boolean;
  onClick: () => void;
}

// Input component with validation
interface InputProps {
  label: string;
  type: 'text' | 'email' | 'password' | 'number';
  value: string;
  onChange: (value: string) => void;
  error?: string;
  required?: boolean;
}
```

**Layout Components:**
- `Header` - Navigation and user menu
- `Sidebar` - Main navigation sidebar
- `Footer` - Site footer
  - Hidden by default. Perhaps can activate to show notifications and status (such as: "generating...")
- `Layout` - Main layout wrapper
- `Container` - Content container with responsive padding

**Data Display Components:**
- `DataTable` - Sortable, filterable data tables
- `Card` - Content cards with consistent styling
- `Badge` - Status indicators and tags
- `Avatar` - User profile images
- `Rating` - Star rating component

### Domain Components

**Content Components:**
- `ContentCard` - Content preview cards
- `ContentList` - List of content items
- `ContentForm` - Content creation/editing form
- `ContentViewer` - Content display component

**Recommendation Components:**
- `RecommendationCard` - Individual recommendation display
- `RecommendationFeed` - List of recommendations
- `RecommendationFeedback` - Rating/feedback component

**User Components:**
- `UserProfile` - User profile display
- `UserStats` - User statistics component
- `UserPreferences` - Preferences configuration form

## State Management

### Global State Structure

```typescript
interface AppState {
  user: {
    currentUser: User | null;
    preferences: UserPreferences | null;
    isAuthenticated: boolean;
  };
  content: {
    items: Content[];
    currentContent: Content | null;
    filters: ContentFilters;
    pagination: PaginationState;
  };
  recommendations: {
    items: Recommendation[];
    loading: boolean;
    lastUpdated: Date | null;
  };
  ui: {
    theme: 'light' | 'dark';
    sidebarOpen: boolean;
    notifications: Notification[];
  };
}
```

### Data Fetching Strategy

**React Query Example:**
```typescript
// hooks/useUsers.ts
export function useUsers(filters?: UserSearchParams) {
  return useQuery({
    queryKey: ['users', filters],
    queryFn: () => userService.searchUsers(filters),
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
}

export function useCreateUser() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: userService.createUser,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['users'] });
    },
  });
}
```

## Routing

### Route Structure

```typescript
// App.tsx or router configuration
const routes = [
  { path: '/', component: HomePage },
  { path: '/content', component: ContentBrowser },
  { path: '/content/:id', component: ContentDetail },
  { path: '/content/create', component: ContentCreate },
  { path: '/recommendations', component: RecommendationFeed },
  { path: '/profile', component: UserProfile },
  { path: '/dashboard', component: Dashboard },
  { path: '/search', component: SearchPage },
];
```

### Navigation Structure

```typescript
// Navigation menu items
const navigationItems = [
  { label: 'Home', path: '/', icon: 'home' },
  { label: 'Content', path: '/content', icon: 'content' },
  { label: 'Recommendations', path: '/recommendations', icon: 'recommend' },
  { label: 'Profile', path: '/profile', icon: 'user' },
  { label: 'Dashboard', path: '/dashboard', icon: 'dashboard' },
];
```

## Development Environment

### Environment Variables

```bash
# .env.local
VITE_API_BASE_URL=http://localhost:8000
VITE_APP_TITLE=Genonaut
VITE_API_TIMEOUT=10000
VITE_ENABLE_DEV_TOOLS=true
```

### Development Commands

```bash
# Start development server
npm run dev

# Build for production
npm run build

# Run tests
npm run test

# Run linting
npm run lint

# Type checking
npm run type-check

# Preview production build
npm run preview
```

## Integration with Backend API

### API Client Configuration

```typescript
// config/api.ts
export const apiConfig = {
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000',
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
};

// Axios interceptors for error handling
axios.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Handle authentication errors
      redirectToLogin();
    }
    return Promise.reject(error);
  }
);
```

### Error Handling

```typescript
// utils/errorHandling.ts
export class ApiError extends Error {
  constructor(
    message: string,
    public status: number,
    public details?: any
  ) {
    super(message);
    this.name = 'ApiError';
  }
}

export function handleApiError(error: any): ApiError {
  if (error.response) {
    return new ApiError(
      error.response.data.detail || 'An error occurred',
      error.response.status,
      error.response.data
    );
  }
  return new ApiError('Network error', 0);
}
```

## Testing Strategy

### Testing Framework Setup: Vitest

```typescript
// vitest.config.ts
export default defineConfig({
  test: {
    environment: 'jsdom',
    setupFiles: ['./src/test/setup.ts'],
    globals: true,
  },
});

// src/test/setup.ts
import '@testing-library/jest-dom';
import { server } from './mocks/server';

beforeAll(() => server.listen());
afterEach(() => server.resetHandlers());
afterAll(() => server.close());
```

### Component Testing

```typescript
// components/__tests__/ContentCard.test.tsx
import { render, screen } from '@testing-library/react';
import { ContentCard } from '../ContentCard';

test('renders content card with title', () => {
  const mockContent = {
    id: 1,
    title: 'Test Content',
    content_type: 'text',
    creator_id: 1,
    is_public: true,
  };

  render(<ContentCard content={mockContent} />);
  
  expect(screen.getByText('Test Content')).toBeInTheDocument();
});
```

### API Mocking (if / as needed)

```typescript
// test/mocks/handlers.ts
import { rest } from 'msw';

export const handlers = [
  rest.get('/api/v1/users/:id', (req, res, ctx) => {
    return res(
      ctx.json({
        id: 1,
        username: 'testuser',
        email: 'test@example.com',
        is_active: true,
      })
    );
  }),
  
  rest.get('/api/v1/content', (req, res, ctx) => {
    return res(
      ctx.json({
        items: [],
        total: 0,
        skip: 0,
        limit: 10,
      })
    );
  }),
];
```

### Testing Framework: Playwright
TODO: add information regarding set up, commands, workflows, etc.

## Deployment

### Build Configuration

```typescript
// vite.config.ts
export default defineConfig({
  plugins: [react()],
  build: {
    outDir: 'dist',
    sourcemap: true,
    rollupOptions: {
      output: {
        manualChunks: {
          vendor: ['react', 'react-dom'],
          router: ['react-router-dom'],
          api: ['axios', '@tanstack/react-query'],
        },
      },
    },
  },
});
```

### Environment-Specific Configuration

```bash
# .env.production
VITE_API_BASE_URL=https://api.genonaut.com
VITE_ENABLE_DEV_TOOLS=false

# .env.staging
VITE_API_BASE_URL=https://staging-api.genonaut.com
VITE_ENABLE_DEV_TOOLS=true
```

## Additional notes on styles
- Dark mode vs Light mode: User should be able to toggle this in settings. Default should be dark.

## Future Enhancements

### Advanced Features

- **Real-time Updates:** WebSocket integration for live notifications
- **Progressive Web App:** Service workers and offline functionality
- **Advanced Analytics:** Data visualization with Chart.js or D3.js
- **Collaborative Features:** Multi-user editing and sharing

### Performance Optimization

- **Code Splitting:** Route-based and component-based code splitting
- **Image Optimization:** Lazy loading and responsive images
- **Caching Strategy:** Service worker caching and API response caching
- **Bundle Analysis:** Regular bundle size monitoring and optimization

### Accessibility

- **WCAG Compliance:** Ensure AA-level accessibility compliance
- **Screen Reader Support:** Proper ARIA labels and semantic HTML
- **Keyboard Navigation:** Full keyboard accessibility

This frontend architecture provides a solid foundation for building a modern, scalable user interface that integrates seamlessly with the Genonaut FastAPI backend.