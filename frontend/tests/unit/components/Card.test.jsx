import React from 'react'
import { render, screen } from '@testing-library/react'
import Card from '../../../src/components/Card'

describe('Card', () => {
  it('renders children', () => {
    render(<Card><div>Card content</div></Card>)
    expect(screen.getByText('Card content')).toBeInTheDocument()
  })

  it('applies default classes', () => {
    const { container } = render(<Card>Content</Card>)
    const card = container.firstChild
    expect(card).toHaveClass('bg-white')
    expect(card).toHaveClass('rounded-xl')
    expect(card).toHaveClass('shadow-sm')
  })

  it('applies additional classes', () => {
    const { container } = render(<Card className="p-8">Content</Card>)
    const card = container.firstChild
    expect(card).toHaveClass('p-8')
  })

  it('supports dark mode classes', () => {
    const { container } = render(<Card className="dark:bg-gray-900">Content</Card>)
    const card = container.firstChild
    expect(card).toHaveClass('dark:bg-gray-900')
  })

  it('calls onClick when clicked', () => {
    const handleClick = vi.fn()
    const { container } = render(<Card onClick={handleClick}>Clickable</Card>)
    const card = container.firstChild
    card.click()
    expect(handleClick).toHaveBeenCalled()
  })
})
