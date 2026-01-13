import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { LanguageProvider, useLanguage } from '@/contexts/LanguageContext';

// Test component that exposes context values
function TestConsumer() {
  const { language, t, toggleLanguage, setLanguage } = useLanguage();

  return (
    <div>
      <span data-testid="language">{language}</span>
      <span data-testid="translation">{t('home.title')}</span>
      <button onClick={toggleLanguage} data-testid="toggle-btn">Toggle</button>
      <button onClick={() => setLanguage('en')} data-testid="set-en-btn">Set English</button>
      <button onClick={() => setLanguage('ko')} data-testid="set-ko-btn">Set Korean</button>
    </div>
  );
}

describe('LanguageContext', () => {
  describe('LanguageProvider', () => {
    it('provides default language as Korean (ko)', () => {
      render(
        <LanguageProvider>
          <TestConsumer />
        </LanguageProvider>
      );

      expect(screen.getByTestId('language')).toHaveTextContent('ko');
    });

    it('provides translation function that returns correct Korean text', () => {
      render(
        <LanguageProvider>
          <TestConsumer />
        </LanguageProvider>
      );

      // Korean translation for home.title is "인생네컷"
      expect(screen.getByTestId('translation')).toHaveTextContent('인생네컷');
    });

    it('toggles language between ko and en', async () => {
      const user = userEvent.setup();

      render(
        <LanguageProvider>
          <TestConsumer />
        </LanguageProvider>
      );

      // Initial state should be Korean
      expect(screen.getByTestId('language')).toHaveTextContent('ko');

      // Toggle to English
      await user.click(screen.getByTestId('toggle-btn'));
      expect(screen.getByTestId('language')).toHaveTextContent('en');

      // Toggle back to Korean
      await user.click(screen.getByTestId('toggle-btn'));
      expect(screen.getByTestId('language')).toHaveTextContent('ko');
    });

    it('updates translations when language changes', async () => {
      const user = userEvent.setup();

      render(
        <LanguageProvider>
          <TestConsumer />
        </LanguageProvider>
      );

      // Should show Korean translation initially
      expect(screen.getByTestId('translation')).toHaveTextContent('인생네컷');

      // Toggle to English
      await user.click(screen.getByTestId('toggle-btn'));

      // Should show English translation
      expect(screen.getByTestId('translation')).toHaveTextContent('4-Cut Photo');
    });

    it('allows setting language directly', async () => {
      const user = userEvent.setup();

      render(
        <LanguageProvider>
          <TestConsumer />
        </LanguageProvider>
      );

      // Set to English
      await user.click(screen.getByTestId('set-en-btn'));
      expect(screen.getByTestId('language')).toHaveTextContent('en');

      // Set back to Korean
      await user.click(screen.getByTestId('set-ko-btn'));
      expect(screen.getByTestId('language')).toHaveTextContent('ko');
    });
  });

  describe('useLanguage hook', () => {
    it('throws error when used outside LanguageProvider', () => {
      // Suppress console.error for this test
      const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});

      expect(() => {
        render(<TestConsumer />);
      }).toThrow('useLanguage must be used within a LanguageProvider');

      consoleSpy.mockRestore();
    });
  });

  describe('translation function (t)', () => {
    it('returns key if translation not found', () => {
      // Suppress console.warn for missing keys
      const consoleSpy = vi.spyOn(console, 'warn').mockImplementation(() => {});

      function MissingKeyConsumer() {
        const { t } = useLanguage();
        return <span data-testid="missing">{t('nonexistent.key' as never)}</span>;
      }

      render(
        <LanguageProvider>
          <MissingKeyConsumer />
        </LanguageProvider>
      );

      expect(screen.getByTestId('missing')).toHaveTextContent('nonexistent.key');
      expect(consoleSpy).toHaveBeenCalledWith('Translation key not found: nonexistent.key');

      consoleSpy.mockRestore();
    });

    it('handles nested translation keys', () => {
      function NestedKeyConsumer() {
        const { t } = useLanguage();
        return (
          <div>
            <span data-testid="nested-1">{t('camera.countdown.title')}</span>
            <span data-testid="nested-2">{t('error.messages.printer_offline')}</span>
          </div>
        );
      }

      render(
        <LanguageProvider>
          <NestedKeyConsumer />
        </LanguageProvider>
      );

      expect(screen.getByTestId('nested-1')).toHaveTextContent('카운트다운 설정');
      expect(screen.getByTestId('nested-2')).toHaveTextContent('프린터가 오프라인입니다');
    });

    it('handles all major translation sections', () => {
      function AllSectionsConsumer() {
        const { t } = useLanguage();
        return (
          <div>
            <span data-testid="app">{t('app.title')}</span>
            <span data-testid="home">{t('home.startButton')}</span>
            <span data-testid="camera">{t('camera.capture')}</span>
            <span data-testid="preview">{t('preview.print')}</span>
            <span data-testid="printing">{t('printing.title')}</span>
            <span data-testid="complete">{t('complete.title')}</span>
            <span data-testid="error">{t('error.retry')}</span>
            <span data-testid="admin">{t('admin.title')}</span>
            <span data-testid="common">{t('common.confirm')}</span>
          </div>
        );
      }

      render(
        <LanguageProvider>
          <AllSectionsConsumer />
        </LanguageProvider>
      );

      // Verify Korean translations
      expect(screen.getByTestId('app')).toHaveTextContent('포토부스');
      expect(screen.getByTestId('home')).toHaveTextContent('시작하기');
      expect(screen.getByTestId('camera')).toHaveTextContent('촬영');
      expect(screen.getByTestId('preview')).toHaveTextContent('인쇄하기');
      expect(screen.getByTestId('printing')).toHaveTextContent('인쇄 중');
      expect(screen.getByTestId('complete')).toHaveTextContent('완료!');
      expect(screen.getByTestId('error')).toHaveTextContent('다시 시도');
      expect(screen.getByTestId('admin')).toHaveTextContent('관리자');
      expect(screen.getByTestId('common')).toHaveTextContent('확인');
    });
  });
});
