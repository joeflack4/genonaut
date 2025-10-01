import { useEffect } from 'react'
import { Button, Card, CardContent, Stack, TextField, Typography } from '@mui/material'
import { useNavigate } from 'react-router-dom'
import { useCurrentUser } from '../../hooks'

export function LoginPage() {
  const { data: currentUser } = useCurrentUser()
  const navigate = useNavigate()

  useEffect(() => {
    if (currentUser) {
      navigate('/dashboard', { replace: true })
    }
  }, [currentUser, navigate])

  return (
    <Stack spacing={3} alignItems="center" component="section" sx={{ mt: 8 }} data-testid="login-page-root">
      <Typography component="h1" variant="h4" fontWeight={600} data-testid="login-title">
        Login
      </Typography>
      <Typography variant="body2" color="text.secondary" data-testid="login-description">
        Authentication is not yet enabled. This is a placeholder screen.
      </Typography>
      <Card sx={{ width: '100%', maxWidth: 420 }} data-testid="login-card">
        <CardContent>
          <Stack spacing={2} data-testid="login-form">
            <TextField
              label="Email"
              type="email"
              fullWidth
              disabled
              placeholder="placeholder@genonaut.ai"
              inputProps={{ 'data-testid': 'login-email-input' }}
            />
            <TextField
              label="Password"
              type="password"
              fullWidth
              disabled
              placeholder="••••••••"
              inputProps={{ 'data-testid': 'login-password-input' }}
            />
            <Button variant="contained" disabled data-testid="login-submit-button">
              Sign in
            </Button>
          </Stack>
        </CardContent>
      </Card>
    </Stack>
  )
}
