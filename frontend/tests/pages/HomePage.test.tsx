import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import { HomePage } from '@/pages/HomePage';
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

describe('HomePage', () => {
  beforeEach(() => {
    mockNavigate.mockClear();
    vi.clearAllMocks();
  });

  describe('rendering', () => {
    it('renders the main title', () => {
      renderWithProviders(<HomePage />);

      // Korean for home.title is '인생네컷'
      expect(screen.getByText('인생네컷')).toBeInTheDocument();
    });

    it('renders the subtitle', () => {
      renderWithProviders(<HomePage />);

      // Korean for home.subtitle
      expect(screen.getByText('4장의 사진으로 추억을 만들어보세요')).toBeInTheDocument();
    });

    it('renders the start button', () => {
      renderWithProviders(<HomePage />);

      // Korean for home.startButton is '시작하기'
      expect(screen.getByText('시작하기')).toBeInTheDocument();
    });

    it('renders the admin link', () => {
      renderWithProviders(<HomePage />);

      // Korean for admin.title is '관리자'
      expect(screen.getByText('관리자')).toBeInTheDocument();
    });

    it('renders 4-cut photo preview grid', () => {
      const { container } = renderWithProviders(<HomePage />);

      // Should have 4 grid cells for the preview
      const gridCells = container.querySelectorAll('.grid-cols-2 > div');
      expect(gridCells).toHaveLength(4);
    });
  });

  describe('start button interaction', () => {
    it('shows loading spinner when clicked', async () => {
      const user = userEvent.setup();
      renderWithProviders(<HomePage />);

      const startButton = screen.getByText('시작하기');
      await user.click(startButton);

      // Should show loading spinner (the button content changes)
      await waitFor(() => {
        expect(screen.getByRole('status')).toBeInTheDocument();
      });
    });

    it('navigates to camera page after successful session creation', async () => {
      const user = userEvent.setup();
      renderWithProviders(<HomePage />);

      const startButton = screen.getByText('시작하기');
      await user.click(startButton);

      await waitFor(() => {
        expect(mockNavigate).toHaveBeenCalledWith('/camera');
      });
    });

    it('stores session ID in sessionStorage', async () => {
      const user = userEvent.setup();
      renderWithProviders(<HomePage />);

      const startButton = screen.getByText('시작하기');
      await user.click(startButton);

      await waitFor(() => {
        expect(window.sessionStorage.setItem).toHaveBeenCalledWith(
          'sessionId',
          expect.stringMatching(/^session-/)
        );
      });
    });

    it('disables button while loading', async () => {
      const user = userEvent.setup();
      renderWithProviders(<HomePage />);

      const startButton = screen.getByText('시작하기');
      await user.click(startButton);

      // Button should be disabled while loading
      expect(startButton).toBeDisabled();
    });
  });

  describe('admin link interaction', () => {
    it('navigates to admin page when clicked', async () => {
      const user = userEvent.setup();
      renderWithProviders(<HomePage />);

      const adminLink = screen.getByText('관리자');
      await user.click(adminLink);

      expect(mockNavigate).toHaveBeenCalledWith('/admin');
    });
  });

  describe('styling', () => {
    it('start button has primary styling', () => {
      renderWithProviders(<HomePage />);

      const startButton = screen.getByText('시작하기');
      expect(startButton).toHaveClass('btn-primary');
    });

    it('title has correct text size', () => {
      renderWithProviders(<HomePage />);

      const title = screen.getByText('인생네컷');
      expect(title).toHaveClass('text-5xl');
    });
  });
});
