import { useState, useCallback, useRef } from 'react'
import { Grid, Paper, Typography, Box, Tabs, Tab, Button, Stack } from '@mui/material'
import { GenerationForm } from '../../components/generation/GenerationForm'
import { GenerationProgress } from '../../components/generation/GenerationProgress'
import { GenerationHistory } from '../../components/generation/GenerationHistory'
import { ErrorBoundary } from '../../components/common/ErrorBoundary'
import type { ComfyUIGenerationResponse } from '../../services/comfyui-service'
import type { GenerationJobResponse } from '../../services/generation-job-service'
import { usePersistedState } from '../../hooks/usePersistedState'

type ActiveGeneration = ComfyUIGenerationResponse | GenerationJobResponse
type TerminalStatus = 'completed' | 'failed' | 'cancelled'

export function GenerationPage() {
  const [currentGeneration, setCurrentGeneration] = usePersistedState<ActiveGeneration | null>(
    'generation:active-job',
    null
  )
  const [refreshHistory, setRefreshHistory] = useState(0)
  const [activeTab, setActiveTab] = useState<'create' | 'history'>('create')
  const [timeoutActive, setTimeoutActive] = useState(false)
  const continueWaitingCallbackRef = useRef<(() => void) | null>(null)

  const handleGenerationStart = (generation: ComfyUIGenerationResponse) => {
    setCurrentGeneration(generation)
    setRefreshHistory(prev => prev + 1)
  }

  const handleGenerationUpdate = useCallback((generation: ActiveGeneration) => {
    setCurrentGeneration(generation)
  }, [setCurrentGeneration])

  const handleContinueWaiting = useCallback(() => {
    if (continueWaitingCallbackRef.current) {
      continueWaitingCallbackRef.current()
    }
  }, [])

  const handleCancelRequest = useCallback(() => {
    setTimeoutActive(false)
    setCurrentGeneration(null)
  }, [setCurrentGeneration])

  const handleContinueWaitingCallbackSet = useCallback((callback: () => void) => {
    continueWaitingCallbackRef.current = callback
  }, [])

  const handleGenerationFinalStatus = useCallback((status: TerminalStatus, generation: ActiveGeneration) => {
    setTimeoutActive(false)
    setCurrentGeneration(generation)
    setRefreshHistory(prev => prev + 1)
  }, [setCurrentGeneration])

  const handleGenerationReset = useCallback(() => {
    setCurrentGeneration(null)
  }, [setCurrentGeneration])

  return (
    <Box component="section" sx={{ pt: 0, pb: 4, width: '100%' }} data-testid="generation-page">
      <Typography variant="h4" component="h1" gutterBottom data-testid="generation-page-title">
        Image Generation
      </Typography>

      <Box sx={{ borderBottom: 1, borderColor: 'divider', mb: 3 }} data-testid="generation-page-tabs">
        <Tabs
          value={activeTab}
          onChange={(_, value) => setActiveTab(value)}
          aria-label="Generation workflow tabs"
          data-testid="generation-tabs"
        >
          <Tab
            label="Create"
            value="create"
            data-testid="create-tab"
          />
          <Tab
            label="History"
            value="history"
            data-testid="history-tab"
          />
        </Tabs>
      </Box>

      {activeTab === 'create' ? (
        <Grid container spacing={3} data-testid="generation-create-layout">
          {/* Generation Form */}
          <Grid size={{ xs: 12, md: 8, lg: 9, xl: 10 }} data-testid="generation-form-column">
            <Paper sx={{ p: 3 }} data-testid="generation-form-card">
              <Typography variant="h6" gutterBottom data-testid="generation-form-title">
                Create New Generation
              </Typography>
              <ErrorBoundary
                fallbackMessage="An error occurred in the generation form. Please refresh the page and try again."
                onReset={() => window.location.reload()}
              >
                <GenerationForm
                  onGenerationStart={handleGenerationStart}
                  onTimeoutChange={setTimeoutActive}
                  onCancelRequest={handleCancelRequest}
                  onContinueWaitingCallback={handleContinueWaitingCallbackSet}
                />
              </ErrorBoundary>
            </Paper>
          </Grid>

          {/* Generation Progress */}
          <Grid size={{ xs: 12, md: 4, lg: 3, xl: 2 }} data-testid="generation-progress-column">
            <Paper sx={{ p: 3, mb: 3 }} data-testid="generation-progress-card">
              <Typography variant="h6" gutterBottom data-testid="generation-progress-title">
                Generation Status
              </Typography>
              {currentGeneration ? (
                <ErrorBoundary
                  fallbackMessage="An error occurred while displaying the generation progress. Please try again."
                  onReset={handleGenerationReset}
                >
                  <GenerationProgress
                    generation={currentGeneration}
                    onGenerationUpdate={handleGenerationUpdate}
                    onStatusFinalized={handleGenerationFinalStatus}
                  />
                </ErrorBoundary>
              ) : (
                <Box
                  display="flex"
                  alignItems="center"
                  justifyContent="center"
                  minHeight={300}
                  color="text.secondary"
                  data-testid="generation-progress-empty"
                >
                  <Typography variant="body1" data-testid="generation-progress-empty-text">
                    Progress will display after generation starts.
                  </Typography>
                </Box>
              )}
            </Paper>

            {/* Timeout Warning */}
            {timeoutActive && (
              <Paper sx={{ p: 2 }} data-testid="timeout-error">
                <Typography variant="subtitle1" gutterBottom>
                  This request is taking longer than expected.
                </Typography>
                <Typography variant="body2" sx={{ mb: 2 }}>
                  The image generation service might be busy. You can continue waiting or cancel the request.
                </Typography>
                <Stack direction={{ xs: 'column', sm: 'row' }} spacing={1}>
                  <Button
                    variant="contained"
                    color="primary"
                    data-testid="continue-waiting-button"
                    onClick={handleContinueWaiting}
                    fullWidth
                  >
                    Continue Waiting
                  </Button>
                  <Button
                    variant="outlined"
                    color="secondary"
                    data-testid="cancel-request-button"
                    onClick={handleCancelRequest}
                    fullWidth
                  >
                    Cancel Request
                  </Button>
                </Stack>
              </Paper>
            )}
          </Grid>
        </Grid>
      ) : (
        <Paper sx={{ p: 3 }} data-testid="generation-history-card">
          <Typography variant="h6" gutterBottom data-testid="generation-history-title">
            Generation History
          </Typography>
          <GenerationHistory key={refreshHistory} />
        </Paper>
      )}
    </Box>
  )
}
