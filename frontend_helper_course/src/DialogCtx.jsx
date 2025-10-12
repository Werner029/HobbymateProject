/* eslint-disable react-refresh/only-export-components */
import { createContext, useContext, useState } from 'react';

const DialogCtx = createContext({
  openId: null,
  setOpen: () => {},
});
export const useDialogCtx = () => useContext(DialogCtx);
export const DialogProvider = ({ children }) => {
  const [openId, setOpen] = useState(null);
  return <DialogCtx.Provider value={{ openId, setOpen }}>{children}</DialogCtx.Provider>;
};
