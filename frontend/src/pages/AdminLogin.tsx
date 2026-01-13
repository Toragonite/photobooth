import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useLanguage } from "../contexts/LanguageContext";
import { adminApi } from "../services/adminApi";

export function AdminLogin() {
  const navigate = useNavigate();
  const { t } = useLanguage();

  const [pin, setPin] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (pin.length < 4) {
      return;
    }

    try {
      setIsLoading(true);
      setError(null);

      const response = await adminApi.login(pin);

      if (response.success && response.data?.token) {
        navigate("/admin/dashboard");
      } else {
        setError(t("admin.login.invalidPin"));
      }
    } catch (err) {
      console.error("Login failed:", err);
      setError(t("admin.login.invalidPin"));
    } finally {
      setIsLoading(false);
    }
  };

  const handlePinInput = (digit: string) => {
    if (pin.length < 6) {
      setPin(pin + digit);
      setError(null);
    }
  };

  const handleBackspace = () => {
    setPin(pin.slice(0, -1));
    setError(null);
  };

  const handleClear = () => {
    setPin("");
    setError(null);
  };

  return (
    <div className="min-h-screen bg-background flex items-center justify-center p-4">
      <div className="card max-w-md w-full">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-primary mb-2">
            {t("admin.login.title")}
          </h1>
          <button
            onClick={() => navigate("/")}
            className="text-text-muted hover:text-primary transition-colors"
          >
            {t("common.back")}
          </button>
        </div>

        {/* PIN display */}
        <div className="flex justify-center gap-3 mb-8">
          {[0, 1, 2, 3].map((i) => (
            <div
              key={i}
              className={`w-12 h-12 rounded-full border-2 flex items-center justify-center
                         transition-colors
                         ${pin.length > i ? "bg-primary border-primary" : "border-gray-300"}`}
            >
              {pin.length > i && (
                <span className="text-white font-bold">*</span>
              )}
            </div>
          ))}
        </div>

        {/* Error message */}
        {error && <p className="text-error text-center mb-4">{error}</p>}

        {/* Number pad */}
        <div className="grid grid-cols-3 gap-4 mb-6">
          {[1, 2, 3, 4, 5, 6, 7, 8, 9].map((digit) => (
            <button
              key={digit}
              onClick={() => handlePinInput(String(digit))}
              className="w-full h-16 text-2xl font-semibold rounded-xl
                        bg-gray-100 hover:bg-gray-200 active:bg-gray-300
                        transition-colors"
            >
              {digit}
            </button>
          ))}
          <button
            onClick={handleClear}
            className="w-full h-16 text-lg font-medium rounded-xl
                      bg-gray-100 hover:bg-gray-200 active:bg-gray-300
                      text-text-muted transition-colors"
          >
            C
          </button>
          <button
            onClick={() => handlePinInput("0")}
            className="w-full h-16 text-2xl font-semibold rounded-xl
                      bg-gray-100 hover:bg-gray-200 active:bg-gray-300
                      transition-colors"
          >
            0
          </button>
          <button
            onClick={handleBackspace}
            className="w-full h-16 text-lg font-medium rounded-xl
                      bg-gray-100 hover:bg-gray-200 active:bg-gray-300
                      text-text-muted transition-colors"
          >
            <svg
              className="w-6 h-6 mx-auto"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M12 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2M3 12l6.414 6.414a2 2 0 001.414.586H19a2 2 0 002-2V7a2 2 0 00-2-2h-8.172a2 2 0 00-1.414.586L3 12z"
              />
            </svg>
          </button>
        </div>

        {/* Submit button */}
        <button
          onClick={handleSubmit}
          disabled={pin.length < 4 || isLoading}
          className="btn-primary w-full"
        >
          {isLoading ? (
            <div className="w-6 h-6 border-2 border-white border-t-transparent rounded-full animate-spin mx-auto" />
          ) : (
            t("admin.login.submit")
          )}
        </button>
      </div>
    </div>
  );
}
