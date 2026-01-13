/**
 * Tests for LoadingSpinner component.
 */

import { render, screen } from '@testing-library/react'
import { describe, it, expect } from 'vitest'
import { LoadingSpinner } from '../../src/components/common/LoadingSpinner'

describe('LoadingSpinner', () => {
  it('renders with default props', () => {
    render(<LoadingSpinner />)

    const spinner = screen.getByRole('status')
    expect(spinner).toBeInTheDocument()
    expect(spinner).toHaveAttribute('aria-label', 'Loading')
  })

  it('renders without message by default', () => {
    render(<LoadingSpinner />)

    // No text should be present
    expect(screen.queryByText(/./)).not.toBeInTheDocument()
  })

  it('displays message when provided', () => {
    render(<LoadingSpinner message="Loading..." />)

    expect(screen.getByText('Loading...')).toBeInTheDocument()
  })

  it('applies small size class', () => {
    render(<LoadingSpinner size="sm" />)

    const spinner = screen.getByRole('status')
    expect(spinner).toHaveClass('h-6', 'w-6')
  })

  it('applies medium size class by default', () => {
    render(<LoadingSpinner />)

    const spinner = screen.getByRole('status')
    expect(spinner).toHaveClass('h-12', 'w-12')
  })

  it('applies large size class', () => {
    render(<LoadingSpinner size="lg" />)

    const spinner = screen.getByRole('status')
    expect(spinner).toHaveClass('h-16', 'w-16')
  })

  it('applies primary color class by default', () => {
    render(<LoadingSpinner />)

    const spinner = screen.getByRole('status')
    expect(spinner).toHaveClass('border-primary')
  })

  it('applies white color class', () => {
    render(<LoadingSpinner color="white" />)

    const spinner = screen.getByRole('status')
    expect(spinner).toHaveClass('border-white')
  })

  it('applies white text color to message when color is white', () => {
    render(<LoadingSpinner color="white" message="Loading..." />)

    const message = screen.getByText('Loading...')
    expect(message).toHaveClass('text-white')
  })

  it('has spinning animation', () => {
    render(<LoadingSpinner />)

    const spinner = screen.getByRole('status')
    expect(spinner).toHaveClass('animate-spin')
  })
})
