import { useLanguage } from "../../contexts/LanguageContext";

export function LanguageToggle() {
  const { language, toggleLanguage, t } = useLanguage();

  return (
    <button
      onClick={toggleLanguage}
      className="touch-target px-3 py-2 rounded-full bg-primary-light text-primary
                 font-medium text-sm hover:bg-primary hover:text-white
                 transition-colors"
      aria-label={t("home.languageToggle")}
    >
      {language === "ko" ? "EN" : "한"}
    </button>
  );
}
