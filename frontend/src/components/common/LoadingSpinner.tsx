interface LoadingSpinnerProps {
  size?: "sm" | "md" | "lg";
  color?: "primary" | "white";
  message?: string;
}

export function LoadingSpinner({
  size = "md",
  color = "primary",
  message,
}: LoadingSpinnerProps) {
  const sizeClasses = {
    sm: "h-6 w-6",
    md: "h-12 w-12",
    lg: "h-16 w-16",
  };

  const colorClasses = {
    primary: "border-primary",
    white: "border-white",
  };

  return (
    <div className="flex flex-col items-center justify-center gap-4">
      <div
        className={`${sizeClasses[size]} border-4 ${colorClasses[color]}
                    border-t-transparent rounded-full animate-spin`}
        role="status"
        aria-label="Loading"
      />
      {message && (
        <p
          className={`text-lg ${color === "white" ? "text-white" : "text-text-muted"}`}
        >
          {message}
        </p>
      )}
    </div>
  );
}
