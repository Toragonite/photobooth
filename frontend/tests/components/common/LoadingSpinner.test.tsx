import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { LoadingSpinner } from '@/components/common/LoadingSpinner';

describe('LoadingSpinner', () => {
  describe('rendering', () => {
    it('renders spinner with default props', () => {
      render(<LoadingSpinner />);

      const spinner = screen.getByRole('status');
      expect(spinner).toBeInTheDocument();
      expect(spinner).toHaveAttribute('aria-label', 'Loading');
    });

    it('renders without message by default', () => {
      render(<LoadingSpinner />);

      expect(screen.queryByRole('paragraph')).not.toBeInTheDocument();
    });

    it('renders message when provided', () => {
      render(<LoadingSpinner message="Please wait..." />);

      expect(screen.getByText('Please wait...')).toBeInTheDocument();
    });
  });

  describe('size variants', () => {
    it('applies small size classes', () => {
      render(<LoadingSpinner size="sm" />);

      const spinner = screen.getByRole('status');
      expect(spinner).toHaveClass('h-6', 'w-6');
    });

    it('applies medium size classes by default', () => {
      render(<LoadingSpinner />);

      const spinner = screen.getByRole('status');
      expect(spinner).toHaveClass('h-12', 'w-12');
    });

    it('applies large size classes', () => {
      render(<LoadingSpinner size="lg" />);

      const spinner = screen.getByRole('status');
      expect(spinner).toHaveClass('h-16', 'w-16');
    });
  });

  describe('color variants', () => {
    it('applies primary color classes by default', () => {
      render(<LoadingSpinner />);

      const spinner = screen.getByRole('status');
      expect(spinner).toHaveClass('border-primary');
    });

    it('applies white color classes', () => {
      render(<LoadingSpinner color="white" />);

      const spinner = screen.getByRole('status');
      expect(spinner).toHaveClass('border-white');
    });

    it('applies correct text color for white spinner message', () => {
      render(<LoadingSpinner color="white" message="Loading..." />);

      const message = screen.getByText('Loading...');
      expect(message).toHaveClass('text-white');
    });

    it('applies correct text color for primary spinner message', () => {
      render(<LoadingSpinner color="primary" message="Loading..." />);

      const message = screen.getByText('Loading...');
      expect(message).toHaveClass('text-text-muted');
    });
  });

  describe('accessibility', () => {
    it('has appropriate role for screen readers', () => {
      render(<LoadingSpinner />);

      expect(screen.getByRole('status')).toBeInTheDocument();
    });

    it('has aria-label for accessibility', () => {
      render(<LoadingSpinner />);

      const spinner = screen.getByRole('status');
      expect(spinner).toHaveAttribute('aria-label', 'Loading');
    });
  });

  describe('animation', () => {
    it('has spin animation class', () => {
      render(<LoadingSpinner />);

      const spinner = screen.getByRole('status');
      expect(spinner).toHaveClass('animate-spin');
    });
  });
});
