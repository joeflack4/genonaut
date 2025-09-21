import type { RouteObject } from 'react-router-dom'
import { Navigate, useRoutes } from 'react-router-dom'
import { AppLayout } from './components/layout'
import { LoginPage, SignupPage } from './pages/auth'
import { ContentPage } from './pages/content'
import { DashboardPage } from './pages/dashboard'
import { RecommendationsPage } from './pages/recommendations'
import { SettingsPage } from './pages/settings'

const routes: RouteObject[] = [
  {
    path: '/',
    element: <AppLayout />,
    children: [
      { index: true, element: <Navigate to="/dashboard" replace /> },
      { path: 'dashboard', element: <DashboardPage /> },
      { path: 'content', element: <ContentPage /> },
      { path: 'recommendations', element: <RecommendationsPage /> },
      { path: 'settings', element: <SettingsPage /> },
    ],
  },
  { path: '/login', element: <LoginPage /> },
  { path: '/signup', element: <SignupPage /> },
  { path: '*', element: <Navigate to="/dashboard" replace /> },
]

export default function App() {
  return useRoutes(routes)
}
