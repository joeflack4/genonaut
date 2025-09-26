import { useState, useRef, useEffect } from 'react'
import type { ReactElement } from 'react'
import { Box, CircularProgress } from '@mui/material'
import { BrokenImage as BrokenImageIcon } from '@mui/icons-material'

interface LazyImageProps {
  src: string
  alt: string
  width?: string | number
  height?: string | number
  placeholder?: ReactElement
  errorFallback?: ReactElement
  className?: string
  style?: React.CSSProperties
  objectFit?: 'contain' | 'cover' | 'fill' | 'none' | 'scale-down'
  threshold?: number
  onLoad?: () => void
  onError?: () => void
}

export function LazyImage({
  src,
  alt,
  width,
  height,
  placeholder,
  errorFallback,
  className,
  style,
  objectFit = 'cover',
  threshold = 0.1,
  onLoad,
  onError,
}: LazyImageProps) {
  const [isLoaded, setIsLoaded] = useState(false)
  const [isIntersecting, setIsIntersecting] = useState(false)
  const [hasError, setHasError] = useState(false)
  const [isLoading, setIsLoading] = useState(false)
  const imgRef = useRef<HTMLImageElement>(null)
  const observerRef = useRef<IntersectionObserver | null>(null)

  // Default placeholder
  const defaultPlaceholder = (
    <Box
      sx={{
        width: width || '100%',
        height: height || '100%',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        bgcolor: 'grey.100',
        color: 'grey.400',
        ...style,
      }}
      className={className}
    >
      <CircularProgress size={24} />
    </Box>
  )

  // Default error fallback
  const defaultErrorFallback = (
    <Box
      sx={{
        width: width || '100%',
        height: height || '100%',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        bgcolor: 'grey.100',
        color: 'grey.400',
        ...style,
      }}
      className={className}
    >
      <BrokenImageIcon />
    </Box>
  )

  // Set up intersection observer
  useEffect(() => {
    if (!imgRef.current) return

    observerRef.current = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setIsIntersecting(true)
          setIsLoading(true)
          // Disconnect observer once image is in view
          if (observerRef.current) {
            observerRef.current.disconnect()
          }
        }
      },
      { threshold }
    )

    observerRef.current.observe(imgRef.current)

    return () => {
      if (observerRef.current) {
        observerRef.current.disconnect()
      }
    }
  }, [threshold])

  // Handle image load
  const handleLoad = () => {
    setIsLoaded(true)
    setIsLoading(false)
    onLoad?.()
  }

  // Handle image error
  const handleError = () => {
    setHasError(true)
    setIsLoading(false)
    onError?.()
  }

  // Show error fallback if there's an error
  if (hasError) {
    return errorFallback || defaultErrorFallback
  }

  // Show placeholder while waiting for intersection or loading
  if (!isIntersecting || (isLoading && !isLoaded)) {
    return (
      <Box ref={imgRef}>
        {placeholder || defaultPlaceholder}
      </Box>
    )
  }

  // Show the actual image
  return (
    <Box
      ref={imgRef}
      sx={{
        width: width || '100%',
        height: height || '100%',
        position: 'relative',
        ...style,
      }}
      className={className}
    >
      <img
        src={src}
        alt={alt}
        onLoad={handleLoad}
        onError={handleError}
        style={{
          width: '100%',
          height: '100%',
          objectFit,
          opacity: isLoaded ? 1 : 0,
          transition: 'opacity 0.3s ease-in-out',
        }}
      />

      {/* Show loading overlay while image is loading */}
      {isLoading && !isLoaded && (
        <Box
          sx={{
            position: 'absolute',
            top: 0,
            left: 0,
            width: '100%',
            height: '100%',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            bgcolor: 'grey.100',
            color: 'grey.400',
          }}
        >
          <CircularProgress size={24} />
        </Box>
      )}
    </Box>
  )
}