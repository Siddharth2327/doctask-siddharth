import { createContext, useContext, useState, type ReactNode } from "react";

const STORAGE_KEY = "docsnary.activeCaseId";

interface CaseContextValue {
  caseId: string;
  setCaseId: (value: string) => void;
}

const CaseContext = createContext<CaseContextValue | null>(null);

export function CaseProvider({ children }: { children: ReactNode }) {
  const [caseId, setCaseIdState] = useState<string>(
    () => localStorage.getItem(STORAGE_KEY) ?? "",
  );

  function setCaseId(value: string) {
    setCaseIdState(value);
    localStorage.setItem(STORAGE_KEY, value);
  }

  return (
    <CaseContext.Provider value={{ caseId, setCaseId }}>
      {children}
    </CaseContext.Provider>
  );
}

export function useCase(): CaseContextValue {
  const context = useContext(CaseContext);

  if (!context) {
    throw new Error("useCase must be used within a CaseProvider");
  }

  return context;
}
