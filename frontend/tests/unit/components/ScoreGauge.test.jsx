import { render, screen } from '@testing-library/react'
import '@testing-library/jest-dom'
import ScoreGauge from '../../../src/components/ScoreGauge'

describe('ScoreGauge', () => {
  it('renders the score value', () => {
    render(<ScoreGauge score={75} />)
    expect(screen.getByText('75')).toBeInTheDocument()
  })

  it('renders label when provided', () => {
    render(<ScoreGauge score={50} label="Privacy Score" />)
    expect(screen.getByText('Privacy Score')).toBeInTheDocument()
  })

  it('renders subtitle when provided', () => {
    render(<ScoreGauge score={50} subtitle="Out of 100" />)
    expect(screen.getByText('Out of 100')).toBeInTheDocument()
  })

  it('clamps score to 0 when negative', () => {
    render(<ScoreGauge score={-10} />)
    expect(screen.getByText('0')).toBeInTheDocument()
  })

  it('clamps score to 100 when over 100', () => {
    render(<ScoreGauge score={150} />)
    expect(screen.getByText('100')).toBeInTheDocument()
  })

  it('applies green color for score >= 80', () => {
    const { container } = render(<ScoreGauge score={90} />)
    const ring = container.querySelector('circle[stroke-dashoffset]')
    expect(ring).toHaveClass('text-green-500')
  })

  it('applies yellow color for score 60-79', () => {
    const { container } = render(<ScoreGauge score={70} />)
    const ring = container.querySelector('circle[stroke-dashoffset]')
    expect(ring).toHaveClass('text-yellow-500')
  })

  it('applies orange color for score 40-59', () => {
    const { container } = render(<ScoreGauge score={50} />)
    const ring = container.querySelector('circle[stroke-dashoffset]')
    expect(ring).toHaveClass('text-orange-500')
  })

  it('applies red color for score < 40', () => {
    const { container } = render(<ScoreGauge score={20} />)
    const ring = container.querySelector('circle[stroke-dashoffset]')
    expect(ring).toHaveClass('text-red-500')
  })

  it('uses custom size', () => {
    const { container } = render(<ScoreGauge score={50} size={200} />)
    const svg = container.querySelector('svg')
    expect(svg).toHaveAttribute('width', '200')
    expect(svg).toHaveAttribute('height', '200')
  })
})
