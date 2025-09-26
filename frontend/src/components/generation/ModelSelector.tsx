import { useState, useEffect } from 'react'
import {
  Box,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Typography,
  Chip,
  Stack,
  Slider,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  List,
  ListItem,
  ListItemText,
  ListItemButton,
  TextField,
  Alert,
  CircularProgress,
} from '@mui/material'
import { Add as AddIcon } from '@mui/icons-material'
import { useComfyUIService } from '../../hooks/useComfyUIService'
import type { LoraModel, AvailableModel } from '../../services/comfyui-service'

interface ModelSelectorProps {
  checkpointModel: string
  onCheckpointChange: (model: string) => void
  loraModels: LoraModel[]
  onLoraModelsChange: (models: LoraModel[]) => void
  sx?: any
}

export function ModelSelector({
  checkpointModel,
  onCheckpointChange,
  loraModels,
  onLoraModelsChange,
  sx,
}: ModelSelectorProps) {
  const [checkpoints, setCheckpoints] = useState<AvailableModel[]>([])
  const [loras, setLoras] = useState<AvailableModel[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [loraDialogOpen, setLoraDialogOpen] = useState(false)
  const [loraSearch, setLoraSearch] = useState('')

  const { listAvailableModels } = useComfyUIService()

  useEffect(() => {
    loadModels()
  }, [])

  const loadModels = async () => {
    setLoading(true)
    setError(null)

    try {
      const [checkpointResponse, loraResponse] = await Promise.all([
        listAvailableModels({ model_type: 'checkpoint', is_active: true }),
        listAvailableModels({ model_type: 'lora', is_active: true }),
      ])

      setCheckpoints(checkpointResponse.items)
      setLoras(loraResponse.items)

      // Auto-select first checkpoint if none selected
      if (!checkpointModel && checkpointResponse.items.length > 0) {
        onCheckpointChange(checkpointResponse.items[0].name)
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load models')
    } finally {
      setLoading(false)
    }
  }

  const addLoraModel = (lora: AvailableModel) => {
    const isAlreadyAdded = loraModels.some(l => l.name === lora.name)
    if (isAlreadyAdded) return

    const newLora: LoraModel = {
      name: lora.name,
      strength_model: 1.0,
      strength_clip: 1.0,
    }

    onLoraModelsChange([...loraModels, newLora])
    setLoraDialogOpen(false)
  }

  const removeLoraModel = (index: number) => {
    const newModels = loraModels.filter((_, i) => i !== index)
    onLoraModelsChange(newModels)
  }

  const updateLoraStrength = (index: number, field: 'strength_model' | 'strength_clip', value: number) => {
    const newModels = loraModels.map((lora, i) =>
      i === index ? { ...lora, [field]: value } : lora
    )
    onLoraModelsChange(newModels)
  }

  const filteredLoras = loras.filter(lora =>
    lora.name.toLowerCase().includes(loraSearch.toLowerCase())
  )

  if (loading) {
    return (
      <Box display="flex" alignItems="center" justifyContent="center" sx={{ py: 2, ...sx }}>
        <CircularProgress size={24} sx={{ mr: 2 }} />
        <Typography>Loading models...</Typography>
      </Box>
    )
  }

  if (error) {
    return (
      <Alert severity="error" sx={sx}>
        {error}
        <Button onClick={loadModels} size="small" sx={{ ml: 1 }}>
          Retry
        </Button>
      </Alert>
    )
  }

  return (
    <Box sx={sx}>
      {/* Checkpoint Model Selection */}
      <FormControl fullWidth sx={{ mb: 2 }} data-testid="model-selector">
        <InputLabel>Checkpoint Model</InputLabel>
        <Select
          value={checkpointModel}
          onChange={(e) => onCheckpointChange(e.target.value)}
          label="Checkpoint Model"
        >
          {checkpoints.map((model) => (
            <MenuItem key={model.id} value={model.name}>
              {model.name}
              {model.description && (
                <Typography variant="caption" color="text.secondary" sx={{ ml: 1 }}>
                  - {model.description}
                </Typography>
              )}
            </MenuItem>
          ))}
        </Select>
      </FormControl>

      {/* LoRA Models */}
      <Box sx={{ mb: 2 }}>
        <Box display="flex" alignItems="center" justifyContent="space-between" sx={{ mb: 1 }}>
          <Typography variant="subtitle2">LoRA Models</Typography>
          <Button
            size="small"
            startIcon={<AddIcon />}
            onClick={() => setLoraDialogOpen(true)}
            variant="outlined"
          >
            Add LoRA
          </Button>
        </Box>

        {loraModels.length > 0 ? (
          <Stack spacing={2}>
            {loraModels.map((lora, index) => (
              <Box key={index} sx={{ p: 2, border: 1, borderColor: 'divider', borderRadius: 1 }}>
                <Box display="flex" alignItems="center" justifyContent="between" sx={{ mb: 1 }}>
                  <Typography variant="body2" fontWeight="medium" sx={{ flex: 1 }}>
                    {lora.name}
                  </Typography>
                  <Chip
                    label="Remove"
                    size="small"
                    color="secondary"
                    variant="outlined"
                    onClick={() => removeLoraModel(index)}
                    clickable
                  />
                </Box>
                <Box sx={{ mt: 1 }}>
                  <Typography variant="caption" gutterBottom>
                    Model Strength: {lora.strength_model.toFixed(2)}
                  </Typography>
                  <Slider
                    value={lora.strength_model}
                    onChange={(_, value) => updateLoraStrength(index, 'strength_model', value as number)}
                    min={-2}
                    max={2}
                    step={0.05}
                    size="small"
                  />
                </Box>
                <Box sx={{ mt: 1 }}>
                  <Typography variant="caption" gutterBottom>
                    CLIP Strength: {lora.strength_clip.toFixed(2)}
                  </Typography>
                  <Slider
                    value={lora.strength_clip}
                    onChange={(_, value) => updateLoraStrength(index, 'strength_clip', value as number)}
                    min={-2}
                    max={2}
                    step={0.05}
                    size="small"
                  />
                </Box>
              </Box>
            ))}
          </Stack>
        ) : (
          <Typography variant="body2" color="text.secondary" sx={{ py: 2 }}>
            No LoRA models selected. Click "Add LoRA" to add one.
          </Typography>
        )}
      </Box>

      {/* LoRA Selection Dialog */}
      <Dialog open={loraDialogOpen} onClose={() => setLoraDialogOpen(false)} maxWidth="md" fullWidth>
        <DialogTitle>Select LoRA Model</DialogTitle>
        <DialogContent>
          <TextField
            fullWidth
            label="Search LoRA models"
            value={loraSearch}
            onChange={(e) => setLoraSearch(e.target.value)}
            sx={{ mb: 2 }}
          />
          <List sx={{ maxHeight: 400, overflow: 'auto' }}>
            {filteredLoras.map((lora) => {
              const isAlreadyAdded = loraModels.some(l => l.name === lora.name)
              return (
                <ListItem key={lora.id} disablePadding>
                  <ListItemButton
                    onClick={() => addLoraModel(lora)}
                    disabled={isAlreadyAdded}
                  >
                    <ListItemText
                      primary={lora.name}
                      secondary={lora.description || 'No description available'}
                    />
                    {isAlreadyAdded && (
                      <Chip label="Added" size="small" color="primary" />
                    )}
                  </ListItemButton>
                </ListItem>
              )
            })}
            {filteredLoras.length === 0 && (
              <ListItem>
                <ListItemText
                  primary="No LoRA models found"
                  secondary={loraSearch ? 'Try a different search term' : 'No LoRA models are available'}
                />
              </ListItem>
            )}
          </List>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setLoraDialogOpen(false)}>Close</Button>
        </DialogActions>
      </Dialog>
    </Box>
  )
}
