import {
  createContext,
  useContext,
  useState,
  useEffect,
  ReactNode,
} from "react";
import { api } from "../services/api";

interface Settings {
  defaultLanguage: string;
  countdownOptions: number[];
  defaultCountdown: number;
  soundEnabled: boolean;
  maxCopies: number;
  logoEnabled: boolean;
  dateFormat: string;
}

interface SettingsContextType {
  settings: Settings;
  isLoading: boolean;
  error: string | null;
  refreshSettings: () => Promise<void>;
}

const defaultSettings: Settings = {
  defaultLanguage: "ko",
  countdownOptions: [3, 5, 8, 10],
  defaultCountdown: 5,
  soundEnabled: true,
  maxCopies: 3,
  logoEnabled: true,
  dateFormat: "YYYY.MM.DD",
};

const SettingsContext = createContext<SettingsContextType | undefined>(
  undefined,
);

interface SettingsProviderProps {
  children: ReactNode;
}

export function SettingsProvider({ children }: SettingsProviderProps) {
  const [settings, setSettings] = useState<Settings>(defaultSettings);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchSettings = async () => {
    try {
      setIsLoading(true);
      setError(null);

      const response = await api.getPublicSettings();

      if (response.success && response.data) {
        const data = response.data;
        setSettings({
          defaultLanguage: data.default_language,
          countdownOptions: data.countdown_options,
          defaultCountdown: data.default_countdown,
          soundEnabled: data.sound_enabled,
          maxCopies: data.max_copies,
          logoEnabled: data.logo_enabled,
          dateFormat: data.date_format,
        });
      }
    } catch (err) {
      console.error("Failed to fetch settings:", err);
      setError("Failed to load settings");
      // Use defaults on error
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchSettings();
  }, []);

  const refreshSettings = async () => {
    await fetchSettings();
  };

  return (
    <SettingsContext.Provider
      value={{ settings, isLoading, error, refreshSettings }}
    >
      {children}
    </SettingsContext.Provider>
  );
}

export function useSettings() {
  const context = useContext(SettingsContext);
  if (context === undefined) {
    throw new Error("useSettings must be used within a SettingsProvider");
  }
  return context;
}
