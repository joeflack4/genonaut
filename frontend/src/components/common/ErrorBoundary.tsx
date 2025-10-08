import { Component, ReactNode } from 'react'
import { Box, Typography, Button, Alert, Paper } from '@mui/material'
import { Error as ErrorIcon } from '@mui/icons-material'

interface ErrorBoundaryProps {
  children: ReactNode
  fallbackMessage?: string
  onReset?: () => void
}

interface ErrorBoundaryState {
  hasError: boolean
  error: Error | null
}

export class ErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  constructor(props: ErrorBoundaryProps) {
    super(props)
    this.state = { hasError: false, error: null }
  }

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { hasError: true, error }
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error('ErrorBoundary caught an error:', error, errorInfo)
  }

  handleReset = () => {
    this.setState({ hasError: false, error: null })
    if (this.props.onReset) {
      this.props.onReset()
    }
  }

  render() {
    if (this.state.hasError) {
      return (
        <Paper sx={{ p: 3, borderColor: 'error.light', borderWidth: 1, borderStyle: 'solid' }}>
          <Box display="flex" flexDirection="column" alignItems="center" gap={2}>
            <ErrorIcon color="error" sx={{ fontSize: 48 }} />
            <Typography variant="h6" color="error">
              Something went wrong
            </Typography>
            <Alert severity="error" sx={{ width: '100%' }}>
              {this.props.fallbackMessage || 'An unexpected error occurred. Please try again.'}
            </Alert>
            {this.state.error && (
              <Typography variant="caption" color="text.secondary" sx={{ fontFamily: 'monospace' }}>
                {this.state.error.message}
              </Typography>
            )}
            <Button
              variant="contained"
              color="primary"
              onClick={this.handleReset}
            >
              Try Again
            </Button>
          </Box>
        </Paper>
      )
    }

    return this.props.children
  }
}
