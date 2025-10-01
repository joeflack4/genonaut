import { useEffect } from 'react'
import { Button, Card, CardContent, Stack, TextField, Typography } from '@mui/material'
import { useNavigate } from 'react-router-dom'
import { useCurrentUser } from '../../hooks'

export function SignupPage() {
  const { data: currentUser } = useCurrentUser()
  const navigate = useNavigate()

  useEffect(() => {
    if (currentUser) {
      navigate('/dashboard', { replace: true })
    }
  }, [currentUser, navigate])

  return (
    <Stack spacing={3} alignItems="center" component="section" sx={{ mt: 8 }} data-testid="signup-page-root">
      <Typography component="h1" variant="h4" fontWeight={600} data-testid="signup-title">
        Sign Up
      </Typography>
      <Typography variant="body2" color="text.secondary" data-testid="signup-description">
        Registration is not yet enabled. This is a placeholder screen.
      </Typography>
      <Card sx={{ width: '100%', maxWidth: 420 }} data-testid="signup-card">
        <CardContent>
          <Stack spacing={2} data-testid="signup-form">
            <TextField
              label="Name"
              fullWidth
              disabled
              placeholder="Admin"
              inputProps={{ 'data-testid': 'signup-name-input' }}
            />
            <TextField
              label="Email"
              type="email"
              fullWidth
              disabled
              placeholder="placeholder@genonaut.ai"
              inputProps={{ 'data-testid': 'signup-email-input' }}
            />
            <TextField
              label="Password"
              type="password"
              fullWidth
              disabled
              placeholder="••••••••"
              inputProps={{ 'data-testid': 'signup-password-input' }}
            />
            <Button variant="contained" disabled data-testid="signup-submit-button">
              Create account
            </Button>
          </Stack>
        </CardContent>
      </Card>
    </Stack>
  )
}
