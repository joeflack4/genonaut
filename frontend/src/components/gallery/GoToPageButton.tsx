import { useState, useRef, useEffect } from 'react'
import { Button, TextField, Box } from '@mui/material'

interface GoToPageButtonProps {
  totalPages: number
  currentPage: number
  onPageChange: (page: number) => void
}

/**
 * "Go to Page" button with input field for direct page navigation.
 *
 * Toggles between button-only and button+input modes:
 * - Initial state: Shows "Go to Page" button
 * - Active state: Shows number input + "Go" button
 */
export function GoToPageButton({ totalPages, currentPage, onPageChange }: GoToPageButtonProps) {
  const [isInputVisible, setIsInputVisible] = useState(false)
  const [inputValue, setInputValue] = useState<string>('')
  const inputRef = useRef<HTMLInputElement>(null)

  // Auto-focus input when shown
  useEffect(() => {
    if (isInputVisible && inputRef.current) {
      inputRef.current.focus()
      inputRef.current.select() // Select text for easy replacement
    }
  }, [isInputVisible])

  const handleButtonClick = () => {
    if (!isInputVisible) {
      // Show input
      setIsInputVisible(true)
      setInputValue('')
    } else {
      // Navigate to page
      handleSubmit()
    }
  }

  const handleSubmit = () => {
    const pageNum = parseInt(inputValue, 10)
    if (!isNaN(pageNum) && pageNum >= 1 && pageNum <= totalPages) {
      onPageChange(pageNum)
      setIsInputVisible(false)
      setInputValue('')
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      handleSubmit()
    } else if (e.key === 'Escape') {
      setIsInputVisible(false)
      setInputValue('')
    }
  }

  return (
    <Box sx={{ display: 'flex', gap: 1, alignItems: 'center' }} data-testid="goto-page-container">
      {isInputVisible && (
        <TextField
          inputRef={inputRef}
          type="number"
          value={inputValue}
          onChange={(e) => setInputValue(e.target.value)}
          onKeyDown={handleKeyDown}
          size="small"
          inputProps={{
            min: 1,
            max: totalPages,
            'data-testid': 'goto-page-input',
          }}
          sx={{ width: '80px' }}
          placeholder={`1-${totalPages}`}
        />
      )}
      <Button
        variant="outlined"
        onClick={handleButtonClick}
        data-testid="goto-page-button"
        size="small"
      >
        {isInputVisible ? 'Go' : 'Go to Page'}
      </Button>
    </Box>
  )
}
