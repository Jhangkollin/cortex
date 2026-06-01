"use client";
import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";

interface CortexDrawerValue {
  drawerOpen: boolean;
  openDrawer: () => void;
  closeDrawer: () => void;
  toggleDrawer: () => void;
  value: string;
  setValue: (v: string) => void;
  model: string;
  setModel: (m: string) => void;
}
const Ctx = createContext<CortexDrawerValue | null>(null);

export function DrawerProvider({ children }: { children: ReactNode }) {
  const [drawerOpen, setOpen] = useState(false);
  const [value, setValue] = useState("");
  const [model, setModel] = useState("auto");
  const openDrawer = useCallback(() => setOpen(true), []);
  const closeDrawer = useCallback(() => setOpen(false), []);
  const toggleDrawer = useCallback(() => setOpen((o) => !o), []);

  useEffect(() => {
    function onKey(e: KeyboardEvent) {
      if (e.key === "Escape") {
        setOpen(false);
        return;
      }
      // Spec §2.2: suppress the ⌘K toggle while typing in an input or
      // textarea (Esc is exempt — handled above so it still closes the
      // drawer from anywhere).
      if (
        e.target instanceof HTMLElement &&
        /^(INPUT|TEXTAREA)$/.test(e.target.tagName)
      ) {
        return;
      }
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "k") {
        e.preventDefault();
        setOpen((o) => !o);
      }
    }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, []);

  const v = useMemo<CortexDrawerValue>(
    () => ({
      drawerOpen,
      openDrawer,
      closeDrawer,
      toggleDrawer,
      value,
      setValue,
      model,
      setModel,
    }),
    [drawerOpen, openDrawer, closeDrawer, toggleDrawer, value, model],
  );
  return <Ctx.Provider value={v}>{children}</Ctx.Provider>;
}

export function useCortexDrawer(): CortexDrawerValue {
  const c = useContext(Ctx);
  if (!c) throw new Error("useCortexDrawer must be used within DrawerProvider");
  return c;
}
