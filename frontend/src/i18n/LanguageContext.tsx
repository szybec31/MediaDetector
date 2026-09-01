import {
  createContext,
  useContext,
  useState,
  type ReactNode,
} from "react";

import pl from "./pl";
import en from "./en";

export type Language = "pl" | "en";

const translations = {
  pl,
  en,
};

interface LanguageContextValue {
  language: Language;
  setLanguage: (language: Language) => void;
  t: typeof pl;
}

const LanguageContext =
  createContext<LanguageContextValue | null>(null);

interface LanguageProviderProps {
  children: ReactNode;
}

export function LanguageProvider({
  children,
}: LanguageProviderProps) {
  const [language, setLanguageState] =
    useState<Language>(() => {
      const savedLanguage = localStorage.getItem(
        "mediadetector-language"
      );

      return savedLanguage === "en" ? "en" : "pl";
    });

  const setLanguage = (newLanguage: Language) => {
    setLanguageState(newLanguage);

    localStorage.setItem(
      "mediadetector-language",
      newLanguage
    );
  };

  const t = translations[language];

  return (
    <LanguageContext.Provider
      value={{
        language,
        setLanguage,
        t,
      }}
    >
      {children}
    </LanguageContext.Provider>
  );
}

export function useLanguage() {
  const context = useContext(LanguageContext);

  if (!context) {
    throw new Error(
      "useLanguage must be used inside LanguageProvider"
    );
  }

  return context;
}