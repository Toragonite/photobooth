/**
 * Session card component for photo gallery
 */
import { useLanguage } from "../../contexts/LanguageContext";

export interface SessionInfo {
  id: string;
  created_at: string;
  status: string;
  language: string;
  has_composite: boolean;
}

interface SessionCardProps {
  session: SessionInfo;
  isSelected: boolean;
  onSelect: (id: string, selected: boolean) => void;
  onClick: (id: string) => void;
  selectionMode: boolean;
}

function StatusBadge({ status }: { status: string }) {
  const { t } = useLanguage();
  const colorMap: Record<string, string> = {
    COMPLETE: "bg-secondary text-white",
    PRINTED: "bg-primary text-white",
    ACTIVE: "bg-warning text-text",
    ABANDONED: "bg-gray-400 text-white",
  };
  const cls = colorMap[status] || "bg-gray-300 text-text";
  const label = t(`admin.gallery.filters.${status.toLowerCase()}`) || status;

  return (
    <span className={`px-2 py-0.5 rounded text-xs font-medium ${cls}`}>
      {label}
    </span>
  );
}

export function SessionCard({
  session,
  isSelected,
  onSelect,
  onClick,
  selectionMode,
}: SessionCardProps) {
  const date = new Date(session.created_at);
  const dateStr = date.toLocaleDateString("ko-KR", {
    month: "numeric",
    day: "numeric",
  });
  const timeStr = date.toLocaleTimeString("ko-KR", {
    hour: "2-digit",
    minute: "2-digit",
  });

  const handleCheckboxClick = (e: React.MouseEvent) => {
    e.stopPropagation();
    onSelect(session.id, !isSelected);
  };

  const handleCardClick = () => {
    if (selectionMode) {
      onSelect(session.id, !isSelected);
    } else {
      onClick(session.id);
    }
  };

  // Composite thumbnail URL
  const thumbnailUrl = session.has_composite
    ? `/api/composite/${session.id}?thumbnail=true`
    : null;

  return (
    <div
      onClick={handleCardClick}
      className={`
        relative rounded-lg overflow-hidden cursor-pointer
        transition-all duration-200 hover:shadow-lg
        ${isSelected ? "ring-2 ring-primary bg-primary/5" : "bg-white shadow"}
      `}
    >
      {/* Checkbox */}
      <div
        className="absolute top-2 left-2 z-10"
        onClick={handleCheckboxClick}
      >
        <div
          className={`
            w-6 h-6 rounded border-2 flex items-center justify-center
            transition-colors duration-200
            ${
              isSelected
                ? "bg-primary border-primary"
                : "bg-white/80 border-gray-300 hover:border-primary"
            }
          `}
        >
          {isSelected && (
            <svg
              className="w-4 h-4 text-white"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={3}
                d="M5 13l4 4L19 7"
              />
            </svg>
          )}
        </div>
      </div>

      {/* Thumbnail */}
      <div className="aspect-[4/6] bg-gray-100 flex items-center justify-center">
        {thumbnailUrl ? (
          <img
            src={thumbnailUrl}
            alt={`Session ${session.id.slice(0, 8)}`}
            className="w-full h-full object-cover"
            loading="lazy"
          />
        ) : (
          <div className="text-gray-400 text-center p-4">
            <svg
              className="w-12 h-12 mx-auto mb-2"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={1.5}
                d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"
              />
            </svg>
            <span className="text-sm">No composite</span>
          </div>
        )}
      </div>

      {/* Info */}
      <div className="p-3 space-y-1">
        <div className="flex items-center justify-between">
          <span className="text-sm font-medium text-text">
            {dateStr} {timeStr}
          </span>
          <StatusBadge status={session.status} />
        </div>
      </div>
    </div>
  );
}
