import { createContext, useContext } from 'react'
import type { Dispatch, SetStateAction } from 'react'
export interface SafetyState { dirty: boolean; busy: boolean }
export const NavigationSafety = createContext<{ safety: SafetyState; setSafety: Dispatch<SetStateAction<SafetyState>> }>({ safety: { dirty: false, busy: false }, setSafety: () => {} })
export const useNavigationSafety = () => useContext(NavigationSafety)
