import { useState, useCallback } from 'react'
import { Grid, Paper, Typography, Box, Tabs, Tab, Alert } from '@mui/material'
import { GenerationForm } from '../../components/generation/GenerationForm'
import { GenerationProgress } from '../../components/generation/GenerationProgress'
import { GenerationHistory } from '../../components/generation/GenerationHistory'
import { ErrorBoundary } from '../../components/common/ErrorBoundary'
import type { ComfyUIGenerationResponse } from '../../services/comfyui-service'
import type { GenerationJobResponse } from '../../services/generation-job-service'
import { usePersistedState } from '../../hooks/usePersistedState'
import { UI_CONFIG } from '../../config/ui'
import { debugLog } from '../../utils/debug'

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

  const handleGenerationStart = (generation: ComfyUIGenerationResponse) => {
    // Key prop on GenerationProgress ensures proper cleanup when ID changes
    setCurrentGeneration(generation)
    setRefreshHistory(prev => prev + 1)
  }

  const handleGenerationUpdate = useCallback((generation: ActiveGeneration) => {
    debugLog.generation('[GenerationPage] Received update from child', {
      id: generation.id,
      status: generation.status,
      updated_at: generation.updated_at,
    })
    setCurrentGeneration(generation)
  }, [setCurrentGeneration])

  const handleCancelRequest = useCallback(() => {
    setTimeoutActive(false)
    setCurrentGeneration(null)
  }, [setCurrentGeneration])

  const handleGenerationFinalStatus = useCallback((status: TerminalStatus, generation: ActiveGeneration) => {
    setTimeoutActive(false)
    setCurrentGeneration(generation)
    setRefreshHistory(prev => prev + 1)
    // State persists until user manually clicks "Clear Details" button
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
          <Grid size={{ xs: 12, md: 7, lg: 9, xl: 9 }} data-testid="generation-form-column">
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
                />
              </ErrorBoundary>
            </Paper>
          </Grid>

          {/* Generation Progress */}
          <Grid size={{ xs: 12, md: 5, lg: 3, xl: 3 }} data-testid="generation-progress-column">
            <Paper sx={{ p: 3, mb: 3 }} data-testid="generation-progress-card">
              <Typography variant="h6" gutterBottom data-testid="generation-progress-title">
                Status
              </Typography>
              {currentGeneration ? (
                <ErrorBoundary
                  fallbackMessage="An error occurred while displaying the generation progress. Please try again."
                  onReset={handleGenerationReset}
                >
                  <GenerationProgress
                    key={currentGeneration.id}
                    generation={currentGeneration}
                    onGenerationUpdate={handleGenerationUpdate}
                    onStatusFinalized={handleGenerationFinalStatus}
                    onClear={handleGenerationReset}
                  />
                </ErrorBoundary>
              ) : (
                <Box
                  color="text.secondary"
                  data-testid="generation-progress-empty"
                >
                  <Typography variant="body1" data-testid="generation-progress-empty-text">
                    Progress will display once generation starts.
                  </Typography>
                </Box>
              )}
            </Paper>

            {/* Timeout Warning */}
            {timeoutActive && (
              <Alert severity="warning" data-testid="timeout-warning">
                <Typography variant="subtitle2" gutterBottom>
                  This request is taking longer than expected.
                </Typography>
                <Typography variant="body2">
                  Image generation is expected to be completed within {UI_CONFIG.GENERATION_TIMEOUT_WARNING_MS / 1000} seconds. You might want to cancel the request and try again.
                </Typography>
              </Alert>
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
