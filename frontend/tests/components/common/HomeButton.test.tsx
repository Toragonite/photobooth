import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import { HomeButton } from '@/components/common/HomeButton';
import { LanguageProvider } from '@/contexts/LanguageContext';

// Mock useNavigate
const mockNavigate = vi.fn();
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  };
});

// Helper to render with providers
function renderWithProviders(ui: React.ReactElement) {
  return render(
    <MemoryRouter>
      <LanguageProvider>{ui}</LanguageProvider>
    </MemoryRouter>
  );
}

describe('HomeButton', () => {
  beforeEach(() => {
    mockNavigate.mockClear();
  });

  describe('rendering', () => {
    it('renders a button', () => {
      renderWithProviders(<HomeButton />);

      expect(screen.getByRole('button')).toBeInTheDocument();
    });

    it('renders home icon (SVG)', () => {
      const { container } = renderWithProviders(<HomeButton />);

      const svg = container.querySelector('svg');
      expect(svg).toBeInTheDocument();
    });

    it('has aria-label for accessibility', () => {
      renderWithProviders(<HomeButton />);

      const button = screen.getByRole('button');
      // Korean for 'common.home' is '홈'
      expect(button).toHaveAttribute('aria-label', '홈');
    });
  });

  describe('interactions', () => {
    it('navigates to home page when clicked', async () => {
      const user = userEvent.setup();
      renderWithProviders(<HomeButton />);

      await user.click(screen.getByRole('button'));

      expect(mockNavigate).toHaveBeenCalledTimes(1);
      expect(mockNavigate).toHaveBeenCalledWith('/');
    });
  });

  describe('styling', () => {
    it('has touch-target class for mobile accessibility', () => {
      renderWithProviders(<HomeButton />);

      const button = screen.getByRole('button');
      expect(button).toHaveClass('touch-target');
    });

    it('has primary color styling', () => {
      renderWithProviders(<HomeButton />);

      const button = screen.getByRole('button');
      expect(button).toHaveClass('text-primary');
    });

    it('has hover transition class', () => {
      renderWithProviders(<HomeButton />);

      const button = screen.getByRole('button');
      expect(button).toHaveClass('transition-colors');
    });
  });

  describe('icon sizing', () => {
    it('icon has correct dimensions', () => {
      const { container } = renderWithProviders(<HomeButton />);

      const svg = container.querySelector('svg');
      expect(svg).toHaveClass('h-8', 'w-8');
    });
  });
});
