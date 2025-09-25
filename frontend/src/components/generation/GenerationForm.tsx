import React, { useState, useEffect } from 'react'
import {
  Box,
  Button,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Chip,
  Alert,
  CircularProgress,
  Grid,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Typography,
  Slider,
  FormControlLabel,
  Switch,
} from '@mui/material'
import { ExpandMore as ExpandMoreIcon } from '@mui/icons-material'
import { ModelSelector } from './ModelSelector'
import { useComfyUIService } from '../../hooks/useComfyUIService'
import type {
  ComfyUIGenerationCreateRequest,
  ComfyUIGenerationResponse,
  LoraModel,
  SamplerParams,
} from '../../services/comfyui-service'

interface GenerationFormProps {
  onGenerationStart: (generation: ComfyUIGenerationResponse) => void
}

const defaultSamplerParams: SamplerParams = {
  seed: -1,
  steps: 20,
  cfg: 7,
  sampler_name: 'euler_ancestral',
  scheduler: 'normal',
  denoise: 1.0,
}

export function GenerationForm({ onGenerationStart }: GenerationFormProps) {
  const [prompt, setPrompt] = useState('')
  const [negativePrompt, setNegativePrompt] = useState('')
  const [checkpointModel, setCheckpointModel] = useState('')
  const [loraModels, setLoraModels] = useState<LoraModel[]>([])
  const [width, setWidth] = useState(832)
  const [height, setHeight] = useState(1216)
  const [batchSize, setBatchSize] = useState(1)
  const [samplerParams, setSamplerParams] = useState<SamplerParams>(defaultSamplerParams)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const { createGeneration } = useComfyUIService()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)

    if (!prompt.trim()) {
      setError('Prompt is required')
      return
    }

    if (!checkpointModel) {
      setError('Please select a checkpoint model')
      return
    }

    setIsSubmitting(true)

    try {
      const request: ComfyUIGenerationCreateRequest = {
        user_id: 'demo-user', // TODO: Get from auth context
        prompt: prompt.trim(),
        negative_prompt: negativePrompt.trim() || undefined,
        checkpoint_model: checkpointModel,
        lora_models: loraModels.length > 0 ? loraModels : undefined,
        width,
        height,
        batch_size: batchSize,
        sampler_params: samplerParams,
      }

      const generation = await createGeneration(request)
      onGenerationStart(generation)

      // Reset form
      setPrompt('')
      setNegativePrompt('')
      setSamplerParams(defaultSamplerParams)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create generation')
    } finally {
      setIsSubmitting(false)
    }
  }

  const updateSamplerParam = (key: keyof SamplerParams, value: any) => {
    setSamplerParams(prev => ({ ...prev, [key]: value }))
  }

  return (
    <Box component="form" onSubmit={handleSubmit} sx={{ width: '100%' }}>
      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      {/* Prompt Fields */}
      <TextField
        fullWidth
        multiline
        rows={4}
        label="Prompt"
        value={prompt}
        onChange={(e) => setPrompt(e.target.value)}
        placeholder="Describe the image you want to generate..."
        required
        sx={{ mb: 2 }}
      />

      <TextField
        fullWidth
        multiline
        rows={2}
        label="Negative Prompt"
        value={negativePrompt}
        onChange={(e) => setNegativePrompt(e.target.value)}
        placeholder="What you don't want in the image..."
        sx={{ mb: 3 }}
      />

      {/* Model Selection */}
      <ModelSelector
        checkpointModel={checkpointModel}
        onCheckpointChange={setCheckpointModel}
        loraModels={loraModels}
        onLoraModelsChange={setLoraModels}
        sx={{ mb: 3 }}
      />

      {/* Basic Parameters */}
      <Grid container spacing={2} sx={{ mb: 3 }}>
        <Grid item xs={6}>
          <TextField
            fullWidth
            type="number"
            label="Width"
            value={width}
            onChange={(e) => setWidth(Number(e.target.value))}
            inputProps={{ min: 64, max: 2048, step: 64 }}
          />
        </Grid>
        <Grid item xs={6}>
          <TextField
            fullWidth
            type="number"
            label="Height"
            value={height}
            onChange={(e) => setHeight(Number(e.target.value))}
            inputProps={{ min: 64, max: 2048, step: 64 }}
          />
        </Grid>
        <Grid item xs={12}>
          <TextField
            fullWidth
            type="number"
            label="Batch Size"
            value={batchSize}
            onChange={(e) => setBatchSize(Number(e.target.value))}
            inputProps={{ min: 1, max: 8 }}
            helperText="Number of images to generate"
          />
        </Grid>
      </Grid>

      {/* Advanced Settings */}
      <Accordion sx={{ mb: 3 }}>
        <AccordionSummary expandIcon={<ExpandMoreIcon />}>
          <Typography>Advanced Settings</Typography>
        </AccordionSummary>
        <AccordionDetails>
          <Grid container spacing={2}>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                type="number"
                label="Seed"
                value={samplerParams.seed}
                onChange={(e) => updateSamplerParam('seed', Number(e.target.value))}
                helperText="-1 for random seed"
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                type="number"
                label="Steps"
                value={samplerParams.steps}
                onChange={(e) => updateSamplerParam('steps', Number(e.target.value))}
                inputProps={{ min: 1, max: 150 }}
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <Typography gutterBottom>CFG Scale: {samplerParams.cfg}</Typography>
              <Slider
                value={samplerParams.cfg}
                onChange={(_, value) => updateSamplerParam('cfg', value)}
                min={1}
                max={20}
                step={0.5}
                marks
                valueLabelDisplay="auto"
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <Typography gutterBottom>Denoise: {samplerParams.denoise}</Typography>
              <Slider
                value={samplerParams.denoise}
                onChange={(_, value) => updateSamplerParam('denoise', value)}
                min={0}
                max={1}
                step={0.01}
                marks
                valueLabelDisplay="auto"
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <FormControl fullWidth>
                <InputLabel>Sampler</InputLabel>
                <Select
                  value={samplerParams.sampler_name}
                  onChange={(e) => updateSamplerParam('sampler_name', e.target.value)}
                >
                  <MenuItem value="euler_ancestral">Euler Ancestral</MenuItem>
                  <MenuItem value="euler">Euler</MenuItem>
                  <MenuItem value="dpmpp_2m">DPM++ 2M</MenuItem>
                  <MenuItem value="dpmpp_sde">DPM++ SDE</MenuItem>
                  <MenuItem value="ddim">DDIM</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} md={6}>
              <FormControl fullWidth>
                <InputLabel>Scheduler</InputLabel>
                <Select
                  value={samplerParams.scheduler}
                  onChange={(e) => updateSamplerParam('scheduler', e.target.value)}
                >
                  <MenuItem value="normal">Normal</MenuItem>
                  <MenuItem value="karras">Karras</MenuItem>
                  <MenuItem value="exponential">Exponential</MenuItem>
                  <MenuItem value="sgm_uniform">SGM Uniform</MenuItem>
                </Select>
              </FormControl>
            </Grid>
          </Grid>
        </AccordionDetails>
      </Accordion>

      <Button
        type="submit"
        variant="contained"
        size="large"
        disabled={isSubmitting || !prompt.trim() || !checkpointModel}
        startIcon={isSubmitting ? <CircularProgress size={20} /> : undefined}
        sx={{ width: '100%' }}
      >
        {isSubmitting ? 'Generating...' : 'Generate Images'}
      </Button>
    </Box>
  )
}