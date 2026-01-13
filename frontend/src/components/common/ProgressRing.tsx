interface ProgressRingProps {
  progress: number;
  size?: number;
  strokeWidth?: number;
  color?: "primary" | "secondary" | "success" | "error";
  backgroundColor?: string;
  showPercentage?: boolean;
  className?: string;
  children?: React.ReactNode;
}

export function ProgressRing({
  progress,
  size = 192,
  strokeWidth = 12,
  color = "primary",
  backgroundColor = "#e5e7eb",
  showPercentage = false,
  className = "",
  children,
}: ProgressRingProps) {
  const colorClasses: Record<string, string> = {
    primary: "#00A1DE",
    secondary: "#20603D",
    success: "#20603D",
    error: "#ef4444",
  };

  const normalizedProgress = Math.min(100, Math.max(0, progress));
  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;
  const strokeDashoffset = circumference - (normalizedProgress / 100) * circumference;
  const center = size / 2;

  return (
    <div
      className={`relative inline-flex items-center justify-center ${className}`}
      style={{ width: size, height: size }}
    >
      <svg
        className="transform -rotate-90"
        width={size}
        height={size}
      >
        {/* Background circle */}
        <circle
          cx={center}
          cy={center}
          r={radius}
          fill="none"
          stroke={backgroundColor}
          strokeWidth={strokeWidth}
        />
        {/* Progress circle */}
        <circle
          cx={center}
          cy={center}
          r={radius}
          fill="none"
          stroke={colorClasses[color]}
          strokeWidth={strokeWidth}
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={strokeDashoffset}
          className="transition-all duration-300 ease-out"
        />
      </svg>

      {/* Center content */}
      <div className="absolute inset-0 flex items-center justify-center">
        {children ? (
          children
        ) : showPercentage ? (
          <span className="text-3xl font-bold text-text">
            {Math.round(normalizedProgress)}%
          </span>
        ) : null}
      </div>
    </div>
  );
}
