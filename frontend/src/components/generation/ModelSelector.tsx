import { useState, useEffect } from 'react'
import {
  Box,
  FormControl,
  FormHelperText,
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
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TablePagination,
  Paper,
  TextField,
  Alert,
  CircularProgress,
  FormControlLabel,
  Switch,
  Grid,
  IconButton,
} from '@mui/material'
import { Add as AddIcon, CheckCircle, Cancel, ArrowUpward, ArrowDownward, Close as CloseIcon, HelpOutline } from '@mui/icons-material'
import { useCheckpointModels } from '../../hooks/useCheckpointModels'
import { useLoraModels as useLoraModelsList } from '../../hooks/useLoraModels'
import type { LoraModel } from '../../services/comfyui-service'
import type { CheckpointModel, LoraModel as LoraModelData } from '../../types/domain'

const clampStrength = (value: number | undefined) => {
  const numeric = typeof value === 'number' ? value : 1.0
  if (Number.isNaN(numeric)) {
    return 1.0
  }
  return Math.min(3, Math.max(0, numeric))
}

const getDisplayNameFromPath = (path: string) => {
  // Extract filename from path and remove extension for display
  // e.g., "loras/Pony/styles/Ghibli_1.safetensors" -> "Ghibli_1"
  const filename = path.split('/').pop() || path
  return filename.replace(/\.(safetensors|pt|ckpt)$/i, '')
}

interface ModelSelectorProps {
  checkpointModel: string
  onCheckpointChange: (model: string) => void
  loraModels: LoraModel[]
  onLoraModelsChange: (models: LoraModel[]) => void
  onAddTriggerWords?: (triggerWords: string[]) => void
  validationError?: string
  sx?: any
}

export function ModelSelector({
  checkpointModel,
  onCheckpointChange,
  loraModels,
  onLoraModelsChange,
  onAddTriggerWords,
  validationError,
  sx,
}: ModelSelectorProps) {
  const [loraDialogOpen, setLoraDialogOpen] = useState(false)
  const [loraSearch, setLoraSearch] = useState('')
  const [loraPage, setLoraPage] = useState(0) // MUI TablePagination uses 0-indexed pages
  const [sortField, setSortField] = useState<'name' | 'rating'>('rating')
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc')
  const [showOnlyCompatible, setShowOnlyCompatible] = useState(false)
  const [showOnlyOptimal, setShowOnlyOptimal] = useState(false)

  const { data: checkpoints, isLoading: checkpointsLoading, error: checkpointsError } = useCheckpointModels()

  // Find the currently selected checkpoint to get its ID
  // checkpointModel contains the path, so match against cp.path
  const selectedCheckpoint = checkpoints?.find(cp => cp.path === checkpointModel)

  // Fetch LoRAs with pagination and checkpoint filtering
  const { data: lorasData, isLoading: lorasLoading, error: lorasError } = useLoraModelsList({
    page: loraPage + 1, // API uses 1-indexed pages
    pageSize: 10,
    checkpointId: selectedCheckpoint?.id,
  })

  const loading = checkpointsLoading || lorasLoading
  const error = checkpointsError || lorasError

  useEffect(() => {
    let needsUpdate = false
    const normalized = loraModels.map(lora => {
      const modelStrength = clampStrength(lora.strength_model)
      const clipStrength = clampStrength(lora.strength_clip)
      if (modelStrength !== lora.strength_model || clipStrength !== lora.strength_clip) {
        needsUpdate = true
        return { ...lora, strength_model: modelStrength, strength_clip: clipStrength }
      }
      return lora
    })

    if (needsUpdate) {
      onLoraModelsChange(normalized)
    }
  }, [loraModels, onLoraModelsChange])

  useEffect(() => {
    // Auto-select first checkpoint if none selected
    if (!checkpointModel && checkpoints && checkpoints.length > 0) {
      // Use path for ComfyUI compatibility (includes subdirectory)
      onCheckpointChange(checkpoints[0].path)
    }
  }, [checkpoints, checkpointModel, onCheckpointChange])

  const addLoraModel = (lora: LoraModelData, keepDialogOpen = false) => {
    // Use path for ComfyUI compatibility (includes subdirectory)
    const loraPath = lora.path
    const isAlreadyAdded = loraModels.some(l => l.name === loraPath)
    if (isAlreadyAdded) return

    const newLora: LoraModel = {
      name: loraPath, // Use path for ComfyUI
      strength_model: 1.0,
      strength_clip: 1.0,
    }

    onLoraModelsChange([...loraModels, newLora])

    // Only close dialog if not keeping it open for multi-select
    if (!keepDialogOpen) {
      setLoraDialogOpen(false)
    }
  }

  const removeLoraModel = (index: number) => {
    const newModels = loraModels.filter((_, i) => i !== index)
    onLoraModelsChange(newModels)
  }

  const removeLoraModelByName = (loraPath: string, keepDialogOpen = false) => {
    const newModels = loraModels.filter(l => l.name !== loraPath)
    onLoraModelsChange(newModels)

    // Only close dialog if not keeping it open for multi-select
    if (!keepDialogOpen) {
      setLoraDialogOpen(false)
    }
  }

  const toggleLoraModel = (lora: LoraModelData, keepDialogOpen = false) => {
    // Use path for ComfyUI compatibility (includes subdirectory)
    const loraPath = lora.path
    const isAlreadyAdded = loraModels.some(l => l.name === loraPath)

    if (isAlreadyAdded) {
      removeLoraModelByName(loraPath, keepDialogOpen)
    } else {
      addLoraModel(lora, keepDialogOpen)
    }
  }

  const updateLoraStrength = (index: number, field: 'strength_model' | 'strength_clip', value: number) => {
    const newModels = loraModels.map((lora, i) =>
      i === index ? { ...lora, [field]: clampStrength(value) } : lora
    )
    onLoraModelsChange(newModels)
  }

  // Reset page when checkpoint changes
  useEffect(() => {
    setLoraPage(0)
  }, [selectedCheckpoint?.id])

  // Reset page when filters change
  useEffect(() => {
    setLoraPage(0)
  }, [showOnlyCompatible, showOnlyOptimal, loraSearch])

  const handleSortChange = (field: 'name' | 'rating') => {
    if (sortField === field) {
      // Toggle sort order if clicking the same field
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc')
    } else {
      // Set new field with its default sort order
      setSortField(field)
      setSortOrder(field === 'rating' ? 'desc' : 'asc')
    }
  }

  const filteredLoras = (lorasData?.items || [])
    .filter(lora => {
      // Search filter - search in both display name and path
      const displayName = lora.name || lora.filename || lora.path
      const path = lora.path
      const searchLower = loraSearch.toLowerCase()
      const matchesSearch = displayName.toLowerCase().includes(searchLower) || path.toLowerCase().includes(searchLower)
      if (!matchesSearch) {
        return false
      }

      // Compatible filter
      if (showOnlyCompatible && lora.isCompatible !== true) {
        return false
      }

      // Optimal filter
      if (showOnlyOptimal && lora.isOptimal !== true) {
        return false
      }

      return true
    })
    .sort((a, b) => {
      let comparison = 0

      if (sortField === 'rating') {
        const ratingA = a.rating ?? 0
        const ratingB = b.rating ?? 0
        comparison = ratingA - ratingB
      } else {
        // Sort by name
        const nameA = (a.name || a.filename || a.path).toLowerCase()
        const nameB = (b.name || b.filename || b.path).toLowerCase()
        comparison = nameA.localeCompare(nameB)
      }

      return sortOrder === 'asc' ? comparison : -comparison
    })

  const handleLoraPageChange = (_event: unknown, newPage: number) => {
    setLoraPage(newPage)
  }

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
        {error instanceof Error ? error.message : 'Failed to load models'}
      </Alert>
    )
  }

  return (
    <Box sx={sx}>
      {/* Checkpoint Model Selection */}
      <FormControl fullWidth sx={{ mb: 2 }} error={!!validationError} data-testid="model-selector">
        <InputLabel>Checkpoint Model</InputLabel>
        <Select
          value={checkpointModel}
          onChange={(e) => onCheckpointChange(e.target.value)}
          label="Checkpoint Model"
        >
          {checkpoints && checkpoints.map((model) => {
            const displayName = model.name || model.filename || model.path
            // Use path as value for ComfyUI compatibility (includes subdirectory)
            const valueForComfyUI = model.path
            return (
              <MenuItem key={model.id} value={valueForComfyUI}>
                {displayName}
                {model.description && (
                  <Typography variant="caption" color="text.secondary" sx={{ ml: 1 }}>
                    - {model.description}
                  </Typography>
                )}
              </MenuItem>
            )
          })}
        </Select>
        {validationError && <FormHelperText>{validationError}</FormHelperText>}
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
          <Grid container spacing={2}>
            {loraModels.map((lora, index) => (
              <Grid size={{ xs: 12, sm: 6, md: 3, lg: 3, xl: 3 }} key={index} sx={{ display: 'flex', minWidth: 0 }}>
                <Box sx={{ p: 2, border: 1, borderColor: 'divider', borderRadius: 1, flex: 1, minWidth: 0, display: 'flex', flexDirection: 'column' }}>
                  <Box display="flex" alignItems="center" sx={{ mb: 1 }}>
                    <Typography variant="body2" fontWeight="medium" sx={{ flex: 1, mr: 1 }}>
                      {getDisplayNameFromPath(lora.name)}
                    </Typography>
                    <IconButton
                      size="small"
                      onClick={() => removeLoraModel(index)}
                      sx={{
                        color: 'text.disabled',
                        p: 0.25,
                        ml: 'auto',
                        '&:hover': {
                          color: 'text.primary',
                          backgroundColor: 'action.hover',
                        },
                      }}
                    >
                      <CloseIcon fontSize="small" />
                    </IconButton>
                  </Box>
                  <Box sx={{ mt: 1 }}>
                    <Typography variant="caption" gutterBottom>
                      Model Strength: {lora.strength_model.toFixed(2)}
                    </Typography>
                    <Slider
                      value={lora.strength_model}
                      onChange={(_, value) => updateLoraStrength(index, 'strength_model', value as number)}
                      min={0}
                      max={3}
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
                      min={0}
                      max={3}
                      step={0.05}
                      size="small"
                    />
                  </Box>
                  {onAddTriggerWords && (() => {
                    // Find the full LoRA data to get trigger words
                    const fullLoraData = lorasData?.items?.find(l => l.path === lora.name)
                    const hasTriggerWords = fullLoraData?.triggerWords && fullLoraData.triggerWords.length > 0

                    if (hasTriggerWords) {
                      return (
                        <Button
                          size="small"
                          variant="outlined"
                          onClick={() => onAddTriggerWords(fullLoraData.triggerWords)}
                          sx={{ mt: 1 }}
                          data-testid={`add-trigger-words-button-${index}`}
                        >
                          Add trigger words
                        </Button>
                      )
                    }
                    return null
                  })()}
                </Box>
              </Grid>
            ))}
          </Grid>
        ) : (
          <Typography variant="body2" color="text.secondary" sx={{ py: 2 }}>
            No LoRA models selected. Click "Add LoRA" to add one.
          </Typography>
        )}
      </Box>

      {/* LoRA Selection Dialog */}
      <Dialog open={loraDialogOpen} onClose={() => setLoraDialogOpen(false)} maxWidth="lg" fullWidth disableRestoreFocus>
        <DialogTitle>Select LoRA Model</DialogTitle>
        <DialogContent>
          <TextField
            fullWidth
            label="Search LoRA models"
            value={loraSearch}
            onChange={(e) => setLoraSearch(e.target.value)}
            sx={{ mb: 1, mt: 1 }}
          />
          <Box sx={{ mb: 2, display: 'flex', gap: 2, alignItems: 'center' }}>
            <FormControlLabel
              control={
                <Switch
                  checked={showOnlyCompatible}
                  onChange={(e) => setShowOnlyCompatible(e.target.checked)}
                />
              }
              label="Only show compatible with checkpoint"
            />
            <FormControlLabel
              control={
                <Switch
                  checked={showOnlyOptimal}
                  onChange={(e) => setShowOnlyOptimal(e.target.checked)}
                />
              }
              label="Only show optimal for checkpoint"
            />
          </Box>
          <Typography variant="caption" color="text.secondary" sx={{ mb: 2, display: 'block' }}>
            Click to select/deselect. Hold Command (Mac) or Alt (Windows) for multiple selections.
          </Typography>
          <TableContainer component={Paper} sx={{ maxHeight: 500 }}>
            <Table stickyHeader>
              <TableHead>
                <TableRow>
                  <TableCell
                    onClick={() => handleSortChange('rating')}
                    sx={{ cursor: 'pointer', userSelect: 'none', width: 100 }}
                  >
                    <Box display="flex" alignItems="center" gap={0.5}>
                      Rating
                      {sortField === 'rating' && (
                        sortOrder === 'asc' ? <ArrowUpward fontSize="small" /> : <ArrowDownward fontSize="small" />
                      )}
                    </Box>
                  </TableCell>
                  <TableCell
                    onClick={() => handleSortChange('name')}
                    sx={{ cursor: 'pointer', userSelect: 'none' }}
                  >
                    <Box display="flex" alignItems="center" gap={0.5}>
                      Name
                      {sortField === 'name' && (
                        sortOrder === 'asc' ? <ArrowUpward fontSize="small" /> : <ArrowDownward fontSize="small" />
                      )}
                    </Box>
                  </TableCell>
                  <TableCell>Description</TableCell>
                  <TableCell>Arch</TableCell>
                  <TableCell>Category</TableCell>
                  <TableCell align="center" sx={{ width: 100 }}>Compatible</TableCell>
                  <TableCell align="center" sx={{ width: 100 }}>Optimal</TableCell>
                  <TableCell align="center" sx={{ width: 100 }}>Selected</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {filteredLoras.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={8} align="center">
                      <Typography variant="body2" color="text.secondary" sx={{ py: 2 }}>
                        {loraSearch ? 'No LoRA models match your search' : 'No LoRA models available'}
                      </Typography>
                    </TableCell>
                  </TableRow>
                ) : (
                  filteredLoras.map((lora) => {
                    const displayName = lora.name || lora.filename || lora.path
                    const loraPath = lora.path
                    const isAlreadyAdded = loraModels.some(l => l.name === loraPath)
                    return (
                      <TableRow
                        key={lora.id}
                        hover
                        onClick={(event) => {
                          // Check if Command (Mac) or Alt (Windows/Linux) key is pressed
                          const keepOpen = event.metaKey || event.altKey
                          toggleLoraModel(lora, keepOpen)
                        }}
                        sx={{
                          cursor: 'pointer',
                          opacity: isAlreadyAdded ? 0.6 : 1,
                        }}
                      >
                        <TableCell>{lora.rating?.toFixed(2) ?? '-'}</TableCell>
                        <TableCell>{displayName}</TableCell>
						{/*<TableCell>{lora.description || 'No description available'}</TableCell>*/}
                        <TableCell>{lora.description || '-'}</TableCell>
                        <TableCell>{lora.compatibleArchitectures || '-'}</TableCell>
                        <TableCell>{lora.family || '-'}</TableCell>
                        <TableCell align="center">
                          {lora.isCompatible === true && <CheckCircle sx={{ color: 'text.primary' }} />}
                          {lora.isCompatible === false && <Cancel sx={{ color: 'text.disabled' }} />}
                          {(lora.isCompatible === null || lora.isCompatible === '') && <HelpOutline sx={{ color: 'text.disabled' }} fontSize="small" />}
                        </TableCell>
                        <TableCell align="center">
                          {lora.isOptimal === true && <CheckCircle sx={{ color: 'text.primary' }} />}
                          {lora.isOptimal === false && <Cancel sx={{ color: 'text.disabled' }} />}
                          {(lora.isOptimal === null || lora.isOptimal === '') && <HelpOutline sx={{ color: 'text.disabled' }} fontSize="small" />}
                        </TableCell>
                        <TableCell align="center">
                          {isAlreadyAdded && <CheckCircle sx={{ color: 'text.primary' }} />}
                        </TableCell>
                      </TableRow>
                    )
                  })
                )}
              </TableBody>
            </Table>
          </TableContainer>
          <TablePagination
            component="div"
            count={lorasData?.pagination?.total || 0}
            page={loraPage}
            onPageChange={handleLoraPageChange}
            rowsPerPage={10}
            rowsPerPageOptions={[10]}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setLoraDialogOpen(false)}>Close</Button>
        </DialogActions>
      </Dialog>
    </Box>
  )
}
