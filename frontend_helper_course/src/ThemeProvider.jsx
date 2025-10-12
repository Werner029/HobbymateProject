/* eslint-disable react-refresh/only-export-components */
import { createContext, useEffect, useState } from 'react';

export const Theme = createContext();

export default function ThemeProvider({ children }) {
  const systemDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
  const [dark, setDark] = useState(
    localStorage.getItem('theme') === 'dark' || (!localStorage.getItem('theme') && systemDark),
  );
  useEffect(() => {
    const root = document.documentElement;
    if (dark) {
      root.classList.add('dark');
      localStorage.setItem('theme', 'dark');
    } else {
      root.classList.remove('dark');
      localStorage.setItem('theme', 'light');
    }
  }, [dark]);

  const toggle = () => setDark((prev) => !prev);

  return <Theme.Provider value={{ dark, toggle }}>{children}</Theme.Provider>;
}
