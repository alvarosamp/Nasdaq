import { createContext, useCallback, useContext, useRef, useState, type ReactNode } from 'react';

type ToastType = 'info' | 'success' | 'error';

interface ToastItem {
  id: number;
  message: string;
  type: ToastType;
  show: boolean;
}

interface ToastContextValue {
  toast: (message: string, type?: ToastType) => void;
}

const ToastContext = createContext<ToastContextValue | null>(null);

export function ToastProvider({ children }: { children: ReactNode }) {
  const [items, setItems] = useState<ToastItem[]>([]);
  const counter = useRef(0);

  const toast = useCallback((message: string, type: ToastType = 'info') => {
    const id = counter.current++;
    setItems((prev) => [...prev, { id, message, type, show: false }]);

    // trigger the fade-in on the next frame, then auto-remove after 4s
    requestAnimationFrame(() => {
      setItems((prev) => prev.map((t) => (t.id === id ? { ...t, show: true } : t)));
    });
    setTimeout(() => {
      setItems((prev) => prev.map((t) => (t.id === id ? { ...t, show: false } : t)));
      setTimeout(() => setItems((prev) => prev.filter((t) => t.id !== id)), 300);
    }, 4000);
  }, []);

  return (
    <ToastContext.Provider value={{ toast }}>
      {children}
      <div className="toast-container">
        {items.map((item) => (
          <div key={item.id} className={`toast toast-${item.type} ${item.show ? 'show' : ''}`}>
            {item.message}
          </div>
        ))}
      </div>
    </ToastContext.Provider>
  );
}

export function useToast(): ToastContextValue['toast'] {
  const ctx = useContext(ToastContext);
  if (!ctx) throw new Error('useToast precisa estar dentro de <ToastProvider>');
  return ctx.toast;
}
