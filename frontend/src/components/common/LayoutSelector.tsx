import { LayoutType, LAYOUT_CONFIGS } from "../../types/layout";
import { useLanguage } from "../../contexts/LanguageContext";

interface LayoutSelectorProps {
  value: LayoutType;
  onChange: (layout: LayoutType) => void;
}

export function LayoutSelector({ value, onChange }: LayoutSelectorProps) {
  const { t } = useLanguage();

  return (
    <div className="flex gap-4 justify-center">
      {/* 1x4 Strip Layout */}
      <button
        onClick={() => onChange("1x4")}
        className={`selection-card flex-1 max-w-[160px] ${
          value === "1x4" ? "selected" : ""
        }`}
      >
        <div className="flex flex-col items-center gap-3">
          {/* Visual representation of 1x4 layout */}
          <div className="flex gap-1">
            {/* Left strip */}
            <div className="flex flex-col gap-0.5">
              {[0, 1, 2, 3].map((i) => (
                <div
                  key={`left-${i}`}
                  className={`w-8 h-5 rounded-sm ${
                    value === "1x4" ? "bg-primary" : "bg-gray-300"
                  }`}
                />
              ))}
            </div>
            {/* Right strip (duplicate) */}
            <div className="flex flex-col gap-0.5">
              {[0, 1, 2, 3].map((i) => (
                <div
                  key={`right-${i}`}
                  className={`w-8 h-5 rounded-sm ${
                    value === "1x4" ? "bg-primary" : "bg-gray-300"
                  }`}
                />
              ))}
            </div>
          </div>
          <div className="text-center">
            <p className={`font-medium text-sm ${value === "1x4" ? "text-primary" : "text-text"}`}>
              {t(LAYOUT_CONFIGS["1x4"].label)}
            </p>
            <p className="text-xs text-text-muted mt-0.5">
              {t(LAYOUT_CONFIGS["1x4"].description)}
            </p>
          </div>
        </div>
      </button>

      {/* 2x2 Grid Layout */}
      <button
        onClick={() => onChange("2x2")}
        className={`selection-card flex-1 max-w-[160px] ${
          value === "2x2" ? "selected" : ""
        }`}
      >
        <div className="flex flex-col items-center gap-3">
          {/* Visual representation of 2x2 layout */}
          <div className="grid grid-cols-2 gap-1">
            {[0, 1, 2, 3].map((i) => (
              <div
                key={i}
                className={`w-8 h-8 rounded-sm ${
                  value === "2x2" ? "bg-primary" : "bg-gray-300"
                }`}
              />
            ))}
          </div>
          <div className="text-center">
            <p className={`font-medium text-sm ${value === "2x2" ? "text-primary" : "text-text"}`}>
              {t(LAYOUT_CONFIGS["2x2"].label)}
            </p>
            <p className="text-xs text-text-muted mt-0.5">
              {t(LAYOUT_CONFIGS["2x2"].description)}
            </p>
          </div>
        </div>
      </button>
    </div>
  );
}
