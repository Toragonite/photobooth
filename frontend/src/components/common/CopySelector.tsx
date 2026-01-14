interface CopySelectorProps {
  value: number;
  onChange: (copies: number) => void;
  max?: number;
  min?: number;
  disabled?: boolean;
  label?: string;
  className?: string;
}

export function CopySelector({
  value,
  onChange,
  max = 3,
  min = 1,
  disabled = false,
  label,
  className = "",
}: CopySelectorProps) {
  const options = Array.from(
    { length: max - min + 1 },
    (_, i) => min + i
  );

  return (
    <div className={`flex flex-col gap-2 ${className}`}>
      {label && (
        <label className="text-sm font-medium text-text-muted">
          {label}
        </label>
      )}
      <div className="flex gap-2">
        {options.map((n) => (
          <button
            key={n}
            type="button"
            onClick={() => onChange(n)}
            disabled={disabled}
            className={`
              w-14 h-14 rounded-lg font-bold text-xl
              transition-all duration-200
              focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2
              ${
                value === n
                  ? "bg-primary text-white shadow-lg scale-105"
                  : "bg-gray-100 text-text hover:bg-gray-200"
              }
              ${disabled ? "opacity-50 cursor-not-allowed" : "cursor-pointer"}
            `}
            aria-pressed={value === n}
            aria-label={`${n} ${n === 1 ? "copy" : "copies"}`}
          >
            {n}
          </button>
        ))}
      </div>
    </div>
  );
}
