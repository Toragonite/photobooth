import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { ErrorDisplay } from '@/components/common/ErrorDisplay';
import { LanguageProvider } from '@/contexts/LanguageContext';

// Helper to render with providers
function renderWithProviders(ui: React.ReactElement) {
  return render(<LanguageProvider>{ui}</LanguageProvider>);
}

describe('ErrorDisplay', () => {
  describe('rendering', () => {
    it('renders with required message prop', () => {
      renderWithProviders(<ErrorDisplay message="An error occurred" />);

      expect(screen.getByText('An error occurred')).toBeInTheDocument();
    });

    it('renders default title from translations when not provided', () => {
      renderWithProviders(<ErrorDisplay message="An error occurred" />);

      // Korean default for 'common.error' is '오류'
      expect(screen.getByText('오류')).toBeInTheDocument();
    });

    it('renders custom title when provided', () => {
      renderWithProviders(
        <ErrorDisplay title="Custom Error Title" message="An error occurred" />
      );

      expect(screen.getByText('Custom Error Title')).toBeInTheDocument();
    });

    it('renders error icon', () => {
      const { container } = renderWithProviders(<ErrorDisplay message="An error occurred" />);

      const svg = container.querySelector('svg');
      expect(svg).toBeInTheDocument();
      expect(svg).toHaveClass('h-8', 'w-8', 'text-error');
    });
  });

  describe('action buttons', () => {
    it('does not render buttons when no callbacks provided', () => {
      renderWithProviders(<ErrorDisplay message="An error occurred" />);

      expect(screen.queryByRole('button')).not.toBeInTheDocument();
    });

    it('renders retry button when onRetry is provided', () => {
      const onRetry = vi.fn();
      renderWithProviders(
        <ErrorDisplay message="An error occurred" onRetry={onRetry} />
      );

      // Korean for 'error.retry' is '다시 시도'
      expect(screen.getByText('다시 시도')).toBeInTheDocument();
    });

    it('renders dismiss button when onDismiss is provided', () => {
      const onDismiss = vi.fn();
      renderWithProviders(
        <ErrorDisplay message="An error occurred" onDismiss={onDismiss} />
      );

      // Korean for 'common.cancel' is '취소'
      expect(screen.getByText('취소')).toBeInTheDocument();
    });

    it('renders both buttons when both callbacks provided', () => {
      const onRetry = vi.fn();
      const onDismiss = vi.fn();
      renderWithProviders(
        <ErrorDisplay
          message="An error occurred"
          onRetry={onRetry}
          onDismiss={onDismiss}
        />
      );

      expect(screen.getByText('다시 시도')).toBeInTheDocument();
      expect(screen.getByText('취소')).toBeInTheDocument();
    });
  });

  describe('interactions', () => {
    it('calls onRetry when retry button is clicked', async () => {
      const user = userEvent.setup();
      const onRetry = vi.fn();

      renderWithProviders(
        <ErrorDisplay message="An error occurred" onRetry={onRetry} />
      );

      await user.click(screen.getByText('다시 시도'));

      expect(onRetry).toHaveBeenCalledTimes(1);
    });

    it('calls onDismiss when dismiss button is clicked', async () => {
      const user = userEvent.setup();
      const onDismiss = vi.fn();

      renderWithProviders(
        <ErrorDisplay message="An error occurred" onDismiss={onDismiss} />
      );

      await user.click(screen.getByText('취소'));

      expect(onDismiss).toHaveBeenCalledTimes(1);
    });
  });

  describe('styling', () => {
    it('has error border styling', () => {
      const { container } = renderWithProviders(
        <ErrorDisplay message="An error occurred" />
      );

      const card = container.querySelector('.card');
      expect(card).toHaveClass('border-error');
    });

    it('has error background color', () => {
      const { container } = renderWithProviders(
        <ErrorDisplay message="An error occurred" />
      );

      const card = container.querySelector('.card');
      expect(card).toHaveClass('bg-red-50');
    });

    it('retry button has primary styling', () => {
      const onRetry = vi.fn();
      renderWithProviders(
        <ErrorDisplay message="An error occurred" onRetry={onRetry} />
      );

      const retryButton = screen.getByText('다시 시도');
      expect(retryButton).toHaveClass('btn-primary');
    });

    it('dismiss button has outline styling', () => {
      const onDismiss = vi.fn();
      renderWithProviders(
        <ErrorDisplay message="An error occurred" onDismiss={onDismiss} />
      );

      const dismissButton = screen.getByText('취소');
      expect(dismissButton).toHaveClass('btn-outline');
    });
  });

  describe('different error messages', () => {
    it('displays printer offline message correctly', () => {
      renderWithProviders(
        <ErrorDisplay
          title="프린터 오류"
          message="프린터가 오프라인입니다. 연결을 확인하세요."
        />
      );

      expect(screen.getByText('프린터 오류')).toBeInTheDocument();
      expect(
        screen.getByText('프린터가 오프라인입니다. 연결을 확인하세요.')
      ).toBeInTheDocument();
    });

    it('displays long error message', () => {
      const longMessage =
        'This is a very long error message that explains in detail what went wrong and provides context for the user to understand the issue better.';
      renderWithProviders(<ErrorDisplay message={longMessage} />);

      expect(screen.getByText(longMessage)).toBeInTheDocument();
    });
  });
});
