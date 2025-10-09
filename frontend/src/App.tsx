import type { RouteObject } from 'react-router-dom'
import { Navigate, useParams, useRoutes } from 'react-router-dom'
import { AppLayout } from './components/layout'
import { LoginPage, SignupPage } from './pages/auth'
import { GalleryPage } from './pages/gallery'
import { DashboardPage } from './pages/dashboard'
import { ImageViewPage } from './pages/view'
import { RecommendationsPage } from './pages/recommendations'
import { SettingsPage } from './pages/settings'
import { GenerationPage } from './pages/generation'
import { TagsPage } from './pages/tags'
import { AdminFlaggedContentPage } from './pages/admin'

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
      { path: 'view/:id', element: <ImageViewPage /> },
      { path: 'recommendations', element: <RecommendationsPage /> },
      { path: 'generate', element: <GenerationPage /> },
      { path: 'generation', element: <GenerationPage /> },
      { path: 'tags', element: <TagsPage /> },
      { path: 'settings', element: <SettingsPage /> },
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
