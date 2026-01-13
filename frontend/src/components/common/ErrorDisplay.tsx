import { useLanguage } from "../../contexts/LanguageContext";

interface ErrorDisplayProps {
  title?: string;
  message: string;
  onRetry?: () => void;
  onDismiss?: () => void;
}

export function ErrorDisplay({
  title,
  message,
  onRetry,
  onDismiss,
}: ErrorDisplayProps) {
  const { t } = useLanguage();

  return (
    <div className="card bg-red-50 border-2 border-error max-w-md mx-auto">
      <div className="flex items-start gap-4">
        {/* Error icon */}
        <div className="flex-shrink-0">
          <svg
            className="h-8 w-8 text-error"
            xmlns="http://www.w3.org/2000/svg"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
            />
          </svg>
        </div>

        {/* Content */}
        <div className="flex-1">
          <h3 className="text-lg font-semibold text-error">
            {title || t("common.error")}
          </h3>
          <p className="mt-1 text-text-muted">{message}</p>

          {/* Actions */}
          {(onRetry || onDismiss) && (
            <div className="mt-4 flex gap-3">
              {onRetry && (
                <button
                  onClick={onRetry}
                  className="btn-primary py-2 px-4 min-h-0 text-sm"
                >
                  {t("error.retry")}
                </button>
              )}
              {onDismiss && (
                <button
                  onClick={onDismiss}
                  className="btn-outline py-2 px-4 min-h-0 text-sm"
                >
                  {t("common.cancel")}
                </button>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
