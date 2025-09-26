import { useState } from 'react'
import { Container, Grid, Paper, Typography, Box, Tabs, Tab } from '@mui/material'
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
    <Container maxWidth="xl" sx={{ py: 4 }} data-testid="generation-page">
      <Typography variant="h4" component="h1" gutterBottom>
        Image Generation
      </Typography>

      <Box sx={{ borderBottom: 1, borderColor: 'divider', mb: 3 }}>
        <Tabs
          value={activeTab}
          onChange={(_, value) => setActiveTab(value)}
          aria-label="Generation workflow tabs"
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
        <Grid container spacing={3}>
          {/* Generation Form */}
          {/* @ts-ignore */}
          <Grid item xs={12} md={6}>
            <Paper sx={{ p: 3 }}>
              <Typography variant="h6" gutterBottom>
                Create New Generation
              </Typography>
              <GenerationForm onGenerationStart={handleGenerationStart} />
            </Paper>
          </Grid>

          {/* Generation Progress */}
          {/* @ts-ignore */}
          <Grid item xs={12} md={6}>
            <Paper sx={{ p: 3 }}>
              <Typography variant="h6" gutterBottom>
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
                >
                  <Typography variant="body1">
                    Start a generation to see progress here
                  </Typography>
                </Box>
              )}
            </Paper>
          </Grid>
        </Grid>
      ) : (
        <Paper sx={{ p: 3 }}>
          <Typography variant="h6" gutterBottom>
            Generation History
          </Typography>
          <GenerationHistory key={refreshHistory} />
        </Paper>
      )}
    </Container>
  )
}
