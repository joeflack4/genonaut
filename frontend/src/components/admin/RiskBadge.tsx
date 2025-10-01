import { Chip, Tooltip } from '@mui/material'
import type { RiskLevel } from '../../types/domain'

interface RiskBadgeProps {
  riskScore: number
  size?: 'small' | 'medium'
  showTooltip?: boolean
}

export function getRiskLevel(score: number): RiskLevel {
  if (score <= 25) return 'low'
  if (score <= 50) return 'medium'
  if (score <= 75) return 'high'
  return 'critical'
}

export function getRiskColor(level: RiskLevel): 'success' | 'warning' | 'error' | 'default' {
  switch (level) {
    case 'low':
      return 'success'
    case 'medium':
      return 'warning'
    case 'high':
    case 'critical':
      return 'error'
    default:
      return 'default'
  }
}

export function getRiskLabel(level: RiskLevel): string {
  switch (level) {
    case 'low':
      return 'Low Risk'
    case 'medium':
      return 'Medium Risk'
    case 'high':
      return 'High Risk'
    case 'critical':
      return 'Critical Risk'
    default:
      return 'Unknown'
  }
}

export function RiskBadge({ riskScore, size = 'small', showTooltip = true }: RiskBadgeProps) {
  const level = getRiskLevel(riskScore)
  const color = getRiskColor(level)
  const label = `${riskScore.toFixed(1)}`

  const chip = (
    <Chip
      label={label}
      color={color}
      size={size}
      sx={{
        fontWeight: 'bold',
        minWidth: 50,
      }}
    />
  )

  if (showTooltip) {
    return (
      <Tooltip
        title={
          <>
            <strong>{getRiskLabel(level)}</strong>
            <br />
            Risk Score: {riskScore.toFixed(2)}
          </>
        }
        arrow
      >
        {chip}
      </Tooltip>
    )
  }

  return chip
}
