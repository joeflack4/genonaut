import { useState } from 'react'
import { Grid, Paper, Typography, Box, Tabs, Tab } from '@mui/material'
import { GenerationForm } from '../../components/generation/GenerationForm'
import { GenerationProgress } from '../../components/generation/GenerationProgress'
import { GenerationHistory } from '../../components/generation/GenerationHistory'
import type { ComfyUIGenerationResponse } from '../../services/comfyui-service'

export function GenerationPage() {
  const [currentGeneration, setCurrentGeneration] = useState<ComfyUIGenerationResponse | null>(null)
  const [refreshHistory, setRefreshHistory] = useState(0)
  const [activeTab, setActiveTab] = useState<'create' | 'history'>('create')

  const handleGenerationStart = (generation: ComfyUIGenerationResponse) => {
    setCurrentGeneration(generation)
    setRefreshHistory(prev => prev + 1)
  }

  const handleGenerationComplete = () => {
    setCurrentGeneration(null)
    setRefreshHistory(prev => prev + 1)
  }

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
              <GenerationForm onGenerationStart={handleGenerationStart} />
            </Paper>
          </Grid>

          {/* Generation Progress */}
          <Grid size={{ xs: 12, md: 4, lg: 3, xl: 2 }} data-testid="generation-progress-column">
            <Paper sx={{ p: 3 }} data-testid="generation-progress-card">
              <Typography variant="h6" gutterBottom data-testid="generation-progress-title">
                Generation Status
              </Typography>
              {currentGeneration ? (
                <GenerationProgress
                  generation={currentGeneration}
                  onComplete={handleGenerationComplete}
                />
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
                    Start a generation to see progress here
                  </Typography>
                </Box>
              )}
            </Paper>
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
