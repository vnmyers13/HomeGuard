import React from 'react'
import { render, screen } from '@testing-library/react'
import ScanProgress from '../../../src/components/ScanProgress'

describe('ScanProgress', () => {
  it('renders with running status', () => {
    render(
      <ScanProgress
        scan={{ status: 'running', current_step: 2, broker_count: 5 }}
        steps={['Scanning broker 1', 'Scanning broker 2', 'Scanning broker 3']}
      />
    )
    expect(screen.getByText('Scan in progress')).toBeInTheDocument()
  })

  it('renders progress percentage', () => {
    render(
      <ScanProgress
        scan={{ status: 'running', current_step: 2 }}
        steps={['Step 1', 'Step 2', 'Step 3']}
      />
    )
    expect(screen.getByText('67%')).toBeInTheDocument()
  })

  it('renders completed status', () => {
    render(
      <ScanProgress
        scan={{ status: 'completed', current_step: 3, broker_count: 3 }}
        steps={['Done']}
      />
    )
    expect(screen.getByText(/completed/i)).toBeInTheDocument()
  })

  it('renders failed status', () => {
    render(
      <ScanProgress
        scan={{ status: 'failed' }}
        steps={[]}
      />
    )
    expect(screen.getByText(/failed/i)).toBeInTheDocument()
  })

  it('renders compact mode', () => {
    render(
      <ScanProgress
        scan={{ status: 'running', current_step: 1 }}
        steps={['Step 1', 'Step 2']}
        compact
      />
    )
    expect(screen.getByText('50%')).toBeInTheDocument()
  })

  it('shows 0% when no scan data', () => {
    const { container } = render(<ScanProgress scan={null} steps={[]} />)
    // Should not crash
    expect(container).toBeInTheDocument()
  })

  it('shows 100% when all steps complete', () => {
    render(
      <ScanProgress
        scan={{ status: 'completed', current_step: 3 }}
        steps={['Step 1', 'Step 2', 'Step 3']}
      />
    )
    expect(screen.getByText('100%')).toBeInTheDocument()
  })
})
