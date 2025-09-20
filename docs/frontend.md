# Frontend Documentation

This document outlines the frontend development approach for Genonaut, including recommended technologies, architecture, and integration with the FastAPI backend.

## Current Status

**🚧 Frontend Development Planned**

The backend API is complete and ready for frontend integration. The frontend implementation is the recommended next development phase for the MVP.

## Technology Recommendations

### Primary Framework Options

**Option 1: React + TypeScript (Recommended)**
- **Advantages:** Large ecosystem, excellent TypeScript support, extensive community
- **Best for:** Complex interactive UIs, real-time features, component reusability
- **Libraries:** React Query (API integration), Material-UI or Chakra UI (components)

**Option 2: Vue.js + TypeScript**
- **Advantages:** Gentle learning curve, excellent documentation, good TypeScript support
- **Best for:** Rapid development, clean template syntax, progressive adoption
- **Libraries:** Pinia (state management), Vuetify or Quasar (components)

**Option 3: Svelte/SvelteKit + TypeScript**
- **Advantages:** Minimal bundle size, excellent performance, simpler state management
- **Best for:** Fast loading times, minimal overhead, modern development experience
- **Libraries:** SvelteKit (full-stack), Tailwind CSS (styling)

### Development Stack

**Build Tools:**
- **Vite** - Fast build tool with excellent TypeScript support
- **ESLint + Prettier** - Code quality and formatting
- **Vitest** - Unit testing framework

**API Integration:**
- **Axios or Fetch** - HTTP client for API requests
- **React Query / TanStack Query** - Data fetching and caching
- **OpenAPI Generator** - Auto-generate TypeScript types from API schema

**Styling:**
- **Tailwind CSS** - Utility-first CSS framework
- **Styled Components** - CSS-in-JS (for React)
- **Component Library** - Material-UI, Chakra UI, or Mantine

**State Management:**
- **React Context + useReducer** (for React)
- **Zustand** (lightweight state management)
- **Pinia** (for Vue.js)

## Architecture Overview

### Application Structure

```
frontend/
├── src/
│   ├── components/           # Reusable UI components
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
├── tests/                   # Test files
└── docs/                    # Frontend documentation
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
- User registration and profile management
- User preferences configuration
- User statistics dashboard

**2. Content Browser**
- Content listing with pagination and filtering
- Content detail views
- Content creation and editing forms
- Content search functionality

**3. Interaction Tracking**
- Automatic interaction tracking (views, clicks)
- Rating and feedback components
- User interaction history

**4. Recommendation Display**
- Personalized recommendation feed
- Recommendation explanation/reasoning
- Recommendation feedback collection

**5. System Dashboard**
- Global statistics visualization
- System health monitoring
- Basic analytics charts

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

### Testing Framework Setup

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

### API Mocking

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

## Future Enhancements

### Advanced Features

- **Real-time Updates:** WebSocket integration for live notifications
- **Progressive Web App:** Service workers and offline functionality
- **Advanced Analytics:** Data visualization with Chart.js or D3.js
- **Collaborative Features:** Multi-user editing and sharing
- **Mobile App:** React Native or Flutter mobile application

### Performance Optimization

- **Code Splitting:** Route-based and component-based code splitting
- **Image Optimization:** Lazy loading and responsive images
- **Caching Strategy:** Service worker caching and API response caching
- **Bundle Analysis:** Regular bundle size monitoring and optimization

### Accessibility

- **WCAG Compliance:** Ensure AA-level accessibility compliance
- **Screen Reader Support:** Proper ARIA labels and semantic HTML
- **Keyboard Navigation:** Full keyboard accessibility
- **Color Contrast:** High contrast themes and color blind considerations

This frontend architecture provides a solid foundation for building a modern, scalable user interface that integrates seamlessly with the Genonaut FastAPI backend.