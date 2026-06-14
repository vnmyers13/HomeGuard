import React from 'react'
import { render, screen } from '@testing-library/react'
import StatusBadge from '../../../src/components/StatusBadge'

describe('StatusBadge', () => {
  it('renders with default styles for unknown status', () => {
    render(<StatusBadge status="unknown">Unknown</StatusBadge>)
    expect(screen.getByText('Unknown')).toBeInTheDocument()
  })

  it('applies correct style for active status', () => {
    render(<StatusBadge status="active">Active</StatusBadge>)
    const badge = screen.getByText('Active')
    expect(badge).toHaveClass('bg-green-100')
  })

  it('applies correct style for failed status', () => {
    render(<StatusBadge status="failed">Failed</StatusBadge>)
    const badge = screen.getByText('Failed')
    expect(badge).toHaveClass('bg-red-100')
  })

  it('applies correct style for pending status', () => {
    render(<StatusBadge status="pending">Pending</StatusBadge>)
    const badge = screen.getByText('Pending')
    expect(badge).toHaveClass('bg-yellow-100')
  })

  it('uses status as label when no children provided', () => {
    render(<StatusBadge status="running" />)
    expect(screen.getByText('running')).toBeInTheDocument()
  })

  it('handles undefined status gracefully', () => {
    render(<StatusBadge />)
    expect(screen.getByText('unknown')).toBeInTheDocument()
  })

  it('applies correct style for submitted status', () => {
    render(<StatusBadge status="submitted">Submitted</StatusBadge>)
    expect(screen.getByText('Submitted')).toHaveClass('bg-blue-100')
  })

  it('applies correct style for confirmed_removed status', () => {
    render(<StatusBadge status="confirmed_removed">Removed</StatusBadge>)
    expect(screen.getByText('Removed')).toHaveClass('bg-green-100')
  })

  it('applies correct style for still_listed status', () => {
    render(<StatusBadge status="still_listed">Still Listed</StatusBadge>)
    expect(screen.getByText('Still Listed')).toHaveClass('bg-red-100')
  })
})
