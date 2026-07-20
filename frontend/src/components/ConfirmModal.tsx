import { createContext, useCallback, useContext, useRef, useState, type ReactNode } from 'react';

interface ConfirmState {
  message: string;
  resolve: (result: boolean) => void;
}

type ConfirmFn = (message: string) => Promise<boolean>;

const ConfirmContext = createContext<ConfirmFn | null>(null);

export function ConfirmProvider({ children }: { children: ReactNode }) {
  const [state, setState] = useState<ConfirmState | null>(null);
  const [show, setShow] = useState(false);
  const resolverRef = useRef<((result: boolean) => void) | null>(null);

  const confirm = useCallback<ConfirmFn>((message) => {
    return new Promise((resolve) => {
      resolverRef.current = resolve;
      setState({ message, resolve });
      requestAnimationFrame(() => setShow(true));
    });
  }, []);

  function close(result: boolean) {
    setShow(false);
    setTimeout(() => setState(null), 200);
    resolverRef.current?.(result);
  }

  return (
    <ConfirmContext.Provider value={confirm}>
      {children}
      {state && (
        <div className={`modal-overlay ${show ? 'show' : ''}`} onClick={() => close(false)}>
          <div className="modal-box" onClick={(e) => e.stopPropagation()}>
            <p>{state.message}</p>
            <div className="modal-actions">
              <button type="button" className="btn-secondary" onClick={() => close(false)}>
                Cancelar
              </button>
              <button type="button" className="btn-danger" onClick={() => close(true)}>
                Confirmar
              </button>
            </div>
          </div>
        </div>
      )}
    </ConfirmContext.Provider>
  );
}

export function useConfirm(): ConfirmFn {
  const ctx = useContext(ConfirmContext);
  if (!ctx) throw new Error('useConfirm precisa estar dentro de <ConfirmProvider>');
  return ctx;
}
