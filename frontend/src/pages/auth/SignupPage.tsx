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
    <Stack spacing={3} alignItems="center" component="section" sx={{ mt: 8 }}>
      <Typography component="h1" variant="h4" fontWeight={600}>
        Sign Up
      </Typography>
      <Typography variant="body2" color="text.secondary">
        Registration is not yet enabled. This is a placeholder screen.
      </Typography>
      <Card sx={{ width: '100%', maxWidth: 420 }}>
        <CardContent>
          <Stack spacing={2}>
            <TextField label="Name" fullWidth disabled placeholder="Admin" />
            <TextField label="Email" type="email" fullWidth disabled placeholder="placeholder@genonaut.ai" />
            <TextField label="Password" type="password" fullWidth disabled placeholder="••••••••" />
            <Button variant="contained" disabled>
              Create account
            </Button>
          </Stack>
        </CardContent>
      </Card>
    </Stack>
  )
}
