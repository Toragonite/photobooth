interface PhotoThumbnailProps {
  src?: string | null;
  index: number;
  isActive?: boolean;
  isClickable?: boolean;
  showPlaceholder?: boolean;
  size?: "sm" | "md" | "lg";
  onClick?: (index: number) => void;
  className?: string;
}

export function PhotoThumbnail({
  src,
  index,
  isActive = false,
  isClickable = true,
  showPlaceholder = true,
  size = "md",
  onClick,
  className = "",
}: PhotoThumbnailProps) {
  const sizeClasses = {
    sm: "w-12 h-12",
    md: "w-16 h-16",
    lg: "w-20 h-20",
  };

  const activeClass = isActive
    ? "border-primary ring-2 ring-primary ring-offset-2"
    : "border-gray-300";

  const clickableClass = isClickable
    ? "cursor-pointer hover:opacity-80 transition-opacity"
    : "";

  const handleClick = () => {
    if (isClickable && onClick) {
      onClick(index);
    }
  };

  return (
    <button
      type="button"
      className={`
        ${sizeClasses[size]}
        ${activeClass}
        ${clickableClass}
        rounded-lg overflow-hidden border-2 bg-gray-100
        focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2
        ${className}
      `}
      onClick={handleClick}
      disabled={!isClickable}
      aria-label={`Photo ${index + 1}`}
    >
      {src ? (
        <img
          src={src}
          alt={`Photo ${index + 1}`}
          className="w-full h-full object-cover"
        />
      ) : showPlaceholder ? (
        <span className="flex items-center justify-center h-full text-gray-400 font-medium">
          {index + 1}
        </span>
      ) : null}
    </button>
  );
}
