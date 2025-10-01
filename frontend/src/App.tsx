import type { RouteObject } from 'react-router-dom'
import { Navigate, useRoutes } from 'react-router-dom'
import { AppLayout } from './components/layout'
import { LoginPage, SignupPage } from './pages/auth'
import { GalleryPage } from './pages/gallery'
import { DashboardPage } from './pages/dashboard'
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
      { path: 'gallery', element: <GalleryPage /> },
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
