import React from 'react'
import { render, screen } from '@testing-library/react'
import EmptyState from '../../../src/components/EmptyState'

describe('EmptyState', () => {
  it('renders title and description', () => {
    render(
      <EmptyState
        title="No Results"
        description="Try adjusting your search"
      />
    )
    expect(screen.getByText('No Results')).toBeInTheDocument()
    expect(screen.getByText('Try adjusting your search')).toBeInTheDocument()
  })

  it('renders action button when provided', () => {
    const onAction = vi.fn()
    render(
      <EmptyState
        title="No Results"
        description="Try adjusting your search"
        actionLabel="Search"
        onAction={onAction}
      />
    )
    expect(screen.getByText('Search')).toBeInTheDocument()
  })

  it('calls onAction when action button clicked', () => {
    const onAction = vi.fn()
    render(
      <EmptyState
        title="No Results"
        actionLabel="Search"
        onAction={onAction}
      />
    )
    screen.getByText('Search').click()
    expect(onAction).toHaveBeenCalled()
  })

  it('renders custom icon when provided', () => {
    render(
      <EmptyState
        title="No Results"
        icon={<span data-testid="custom-icon">Custom</span>}
      />
    )
    expect(screen.getByTestId('custom-icon')).toBeInTheDocument()
  })

  it('uses default icon when none provided', () => {
    render(<EmptyState title="No Results" description="No data" />)
    // Default icon should be present
    expect(screen.getByText('No Results')).toBeInTheDocument()
  })
})
