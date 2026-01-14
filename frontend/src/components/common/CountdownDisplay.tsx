interface CountdownDisplayProps {
  count: number;
  size?: "sm" | "md" | "lg" | "xl";
  variant?: "overlay" | "inline";
  showAnimation?: boolean;
  className?: string;
}

export function CountdownDisplay({
  count,
  size = "lg",
  variant = "inline",
  showAnimation = true,
  className = "",
}: CountdownDisplayProps) {
  const sizeClasses = {
    sm: "text-4xl",
    md: "text-6xl",
    lg: "text-8xl",
    xl: "text-9xl",
  };

  const animationClass = showAnimation ? "animate-pulse" : "";

  if (variant === "overlay") {
    return (
      <div
        className={`absolute inset-0 flex items-center justify-center bg-black/50 z-10 ${className}`}
      >
        <span
          className={`${sizeClasses[size]} font-bold text-white ${animationClass}`}
        >
          {count}
        </span>
      </div>
    );
  }

  return (
    <div className={`flex items-center justify-center ${className}`}>
      <span
        className={`${sizeClasses[size]} font-bold text-primary ${animationClass}`}
      >
        {count}
      </span>
    </div>
  );
}
