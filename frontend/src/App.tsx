import { lazy, Suspense } from 'react'
import type { RouteObject } from 'react-router-dom'
import { Navigate, useParams, useRoutes } from 'react-router-dom'
import { CircularProgress, Box } from '@mui/material'
import { AppLayout } from './components/layout'
import { LoginPage, SignupPage } from './pages/auth'
import { GalleryPage } from './pages/gallery'
import { DashboardPage } from './pages/dashboard'
import { ImageViewPage } from './pages/view'
import { RecommendationsPage } from './pages/recommendations'
import { SettingsPage } from './pages/settings'
import { SearchHistoryPage } from './pages/settings/SearchHistoryPage'
import { GenerationPage } from './pages/generation'
import { TagsPage, TagDetailPage } from './pages/tags'
import { AdminFlaggedContentPage } from './pages/admin'
import { NotificationsPage, NotificationDetailPage } from './pages/notifications'
import { BookmarksPage, BookmarksCategoryPage } from './pages/bookmarks'

// Lazy load Analytics page for code splitting (contains heavy charting library)
const AnalyticsPage = lazy(() => import('./pages/settings/AnalyticsPage').then(module => ({ default: module.AnalyticsPage })))

// Loading fallback component
const PageLoader = () => (
  <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '50vh' }}>
    <CircularProgress />
  </Box>
)

const routes: RouteObject[] = [
  {
    path: '/',
    element: <AppLayout />,
    children: [
      { index: true, element: <Navigate to="/dashboard" replace /> },
      { path: 'dashboard', element: <DashboardPage /> },
      { path: 'dashboard/:id', element: <LegacyViewRedirect /> },
      { path: 'gallery', element: <GalleryPage /> },
      { path: 'gallery/:id', element: <LegacyViewRedirect /> },
      { path: 'bookmarks', element: <BookmarksPage /> },
      { path: 'bookmarks/:categoryId', element: <BookmarksCategoryPage /> },
      { path: 'view/:id', element: <ImageViewPage /> },
      { path: 'recommendations', element: <RecommendationsPage /> },
      { path: 'generate', element: <GenerationPage /> },
      { path: 'generate/history', element: <GenerationPage /> },
      { path: 'generation', element: <Navigate to="/generate" replace /> },
      { path: 'tags', element: <TagsPage /> },
      { path: 'tags/:tagId', element: <TagDetailPage /> },
      { path: 'notifications', element: <NotificationsPage /> },
      { path: 'notification/:id', element: <NotificationDetailPage /> },
      { path: 'settings', element: <SettingsPage /> },
      { path: 'settings/search-history', element: <SearchHistoryPage /> },
      { path: 'settings/analytics', element: <Suspense fallback={<PageLoader />}><AnalyticsPage /></Suspense> },
      { path: 'admin/flagged-content', element: <AdminFlaggedContentPage /> },
    ],
  },
  { path: '/login', element: <LoginPage /> },
  { path: '/signup', element: <SignupPage /> },
  { path: '*', element: <Navigate to="/dashboard" replace /> },
]

export default function App() {
  return useRoutes(routes)
}

function LegacyViewRedirect() {
  const params = useParams<{ id: string }>()
  const targetId = params.id ?? ''
  return <Navigate to={`/view/${targetId}`} replace />
}
