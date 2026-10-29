import { createContext, useCallback, useContext, useEffect, useState, type ReactNode } from "react";

type Theme = "dark" | "light";
const KEY = "radix-theme";
const Ctx = createContext<{ theme: Theme; toggle: () => void }>({ theme: "dark", toggle: () => {} });

export function ThemeProvider({ children }: { children: ReactNode }) {
  const [theme, setTheme] = useState<Theme>("dark");

  // Restore the stored theme on boot; CRED dark is the default.
  useEffect(() => {
    const stored = localStorage.getItem(KEY);
    const next: Theme = stored === "light" ? "light" : "dark";
    const el = document.documentElement;
    el.classList.remove("light", "dark");
    if (next === "light") el.classList.add("light");
    setTheme(next);
  }, []);

  const toggle = useCallback(() => {
    setTheme((t) => {
      const next: Theme = t === "dark" ? "light" : "dark";
      const el = document.documentElement;
      el.classList.add("theme-anim");
      el.classList.remove("dark", "light");
      el.classList.add(next);
      localStorage.setItem(KEY, next);
      setTimeout(() => el.classList.remove("theme-anim"), 350);
      return next;
    });
  }, []);

  return <Ctx.Provider value={{ theme, toggle }}>{children}</Ctx.Provider>;
}

export const useTheme = () => useContext(Ctx);
