import React from 'react'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import Modal from '../../../src/components/Modal'

describe('Modal', () => {
  const onClose = vi.fn()

  it('does not render when closed', () => {
    render(<Modal isOpen={false} onClose={onClose}>Content</Modal>)
    expect(screen.queryByText('Content')).not.toBeInTheDocument()
  })

  it('renders when open', () => {
    render(<Modal isOpen={true} onClose={onClose} title="Test Modal">Content</Modal>)
    expect(screen.getByText('Content')).toBeInTheDocument()
    expect(screen.getByText('Test Modal')).toBeInTheDocument()
  })

  it('closes on backdrop click', () => {
    render(<Modal isOpen={true} onClose={onClose}>Content</Modal>)
    const backdrop = document.querySelector('.bg-black\\/50') || document.querySelector('[onClick]')
    fireEvent.click(backdrop)
    expect(onClose).toHaveBeenCalled()
  })

  it('closes on Escape key', () => {
    render(<Modal isOpen={true} onClose={onClose}>Content</Modal>)
    fireEvent.keyDown(window, { key: 'Escape' })
    expect(onClose).toHaveBeenCalled()
  })

  it('closes on X button click', () => {
    render(<Modal isOpen={true} onClose={onClose} title="Test">Content</Modal>)
    const closeBtn = document.querySelector('button')
    fireEvent.click(closeBtn)
    expect(onClose).toHaveBeenCalled()
  })

  it('renders footer when provided', () => {
    render(
      <Modal isOpen={true} onClose={onClose} footer={
        <button>Close</button>
      }>
        Content
      </Modal>
    )
    expect(screen.getByText('Close')).toBeInTheDocument()
  })

  it('does not render footer when not provided', () => {
    render(<Modal isOpen={true} onClose={onClose}>Content</Modal>)
    expect(screen.queryByText('Close')).not.toBeInTheDocument()
  })

  it('supports different sizes', () => {
    const { container } = render(<Modal isOpen={true} onClose={onClose} size="lg">Content</Modal>)
    const modal = container.querySelector('.relative.w-full')
    expect(modal).toHaveClass('max-w-lg')
  })

  it('prevents body scroll when open', () => {
    const originalOverflow = document.body.style.overflow
    render(<Modal isOpen={true} onClose={onClose}>Content</Modal>)
    expect(document.body.style.overflow).toBe('hidden')
  })
})
