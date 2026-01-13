import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { LanguageToggle } from '@/components/common/LanguageToggle';
import { LanguageProvider } from '@/contexts/LanguageContext';

// Helper to render with providers
function renderWithProviders(ui: React.ReactElement) {
  return render(<LanguageProvider>{ui}</LanguageProvider>);
}

describe('LanguageToggle', () => {
  describe('rendering', () => {
    it('renders a button', () => {
      renderWithProviders(<LanguageToggle />);

      expect(screen.getByRole('button')).toBeInTheDocument();
    });

    it('shows "EN" when language is Korean (default)', () => {
      renderWithProviders(<LanguageToggle />);

      expect(screen.getByRole('button')).toHaveTextContent('EN');
    });

    it('has aria-label from translations', () => {
      renderWithProviders(<LanguageToggle />);

      const button = screen.getByRole('button');
      // Korean for 'home.languageToggle' is 'English'
      expect(button).toHaveAttribute('aria-label', 'English');
    });
  });

  describe('toggle behavior', () => {
    it('toggles to Korean display when clicked', async () => {
      const user = userEvent.setup();
      renderWithProviders(<LanguageToggle />);

      const button = screen.getByRole('button');
      expect(button).toHaveTextContent('EN');

      await user.click(button);

      // After toggling to English, should show Korean character '한'
      expect(button).toHaveTextContent('한');
    });

    it('toggles back to English display when clicked twice', async () => {
      const user = userEvent.setup();
      renderWithProviders(<LanguageToggle />);

      const button = screen.getByRole('button');

      await user.click(button); // ko -> en
      expect(button).toHaveTextContent('한');

      await user.click(button); // en -> ko
      expect(button).toHaveTextContent('EN');
    });

    it('updates aria-label after toggle', async () => {
      const user = userEvent.setup();
      renderWithProviders(<LanguageToggle />);

      const button = screen.getByRole('button');

      // Initial state (Korean mode) - aria-label says "English" (switch to English)
      expect(button).toHaveAttribute('aria-label', 'English');

      await user.click(button);

      // After toggle (English mode) - aria-label says "한국어" (switch to Korean)
      expect(button).toHaveAttribute('aria-label', '한국어');
    });
  });

  describe('styling', () => {
    it('has touch-target class for mobile accessibility', () => {
      renderWithProviders(<LanguageToggle />);

      const button = screen.getByRole('button');
      expect(button).toHaveClass('touch-target');
    });

    it('has rounded-full class for pill shape', () => {
      renderWithProviders(<LanguageToggle />);

      const button = screen.getByRole('button');
      expect(button).toHaveClass('rounded-full');
    });

    it('has primary background color', () => {
      renderWithProviders(<LanguageToggle />);

      const button = screen.getByRole('button');
      expect(button).toHaveClass('bg-primary-light');
    });

    it('has transition class for hover effect', () => {
      renderWithProviders(<LanguageToggle />);

      const button = screen.getByRole('button');
      expect(button).toHaveClass('transition-colors');
    });

    it('has appropriate padding', () => {
      renderWithProviders(<LanguageToggle />);

      const button = screen.getByRole('button');
      expect(button).toHaveClass('px-3', 'py-2');
    });
  });

  describe('multiple instances', () => {
    it('all instances stay in sync (share context)', async () => {
      const user = userEvent.setup();

      render(
        <LanguageProvider>
          <LanguageToggle />
          <LanguageToggle />
        </LanguageProvider>
      );

      const buttons = screen.getAllByRole('button');
      expect(buttons).toHaveLength(2);

      // Both should show 'EN' initially
      expect(buttons[0]).toHaveTextContent('EN');
      expect(buttons[1]).toHaveTextContent('EN');

      // Click first button
      await user.click(buttons[0]);

      // Both should now show '한'
      expect(buttons[0]).toHaveTextContent('한');
      expect(buttons[1]).toHaveTextContent('한');
    });
  });
});
