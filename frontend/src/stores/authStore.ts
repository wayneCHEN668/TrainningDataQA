import { create } from "zustand";
import type { UserInfo } from "../types/auth";

interface AuthState {
  user: UserInfo | null;
  token: string | null;
  isAuthenticated: boolean;

  /** 登录成功：保存 token 和用户信息 */
  login: (token: string, user: UserInfo) => void;

  /** 退出：清除所有认证状态 */
  logout: () => void;

  /** 从 localStorage 恢复登录态 */
  hydrate: () => void;
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  token: null,
  isAuthenticated: false,

  login: (token: string, user: UserInfo) => {
    localStorage.setItem("access_token", token);
    set({ token, user, isAuthenticated: true });
  },

  logout: () => {
    localStorage.removeItem("access_token");
    set({ token: null, user: null, isAuthenticated: false });
  },

  hydrate: () => {
    const token = localStorage.getItem("access_token");
    if (token) {
      set({ token, isAuthenticated: true });
    }
  },
}));
