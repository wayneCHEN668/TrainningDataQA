import { useEffect, useState } from "react";
import { Navigate, Outlet } from "react-router-dom";
import { useAuthStore } from "../../stores/authStore";
import type { UserInfo } from "../../types/auth";

export function ProtectedRoute() {
  const token = localStorage.getItem("access_token");
  const { user, login, logout } = useAuthStore();
  const [checking, setChecking] = useState(!user);

  useEffect(() => {
    if (!token) return;
    if (user) {
      setChecking(false);
      return;
    }

    // Token exists but user info not loaded — fetch /me
    let cancelled = false;
    fetch("/api/v1/auth/me", {
      headers: { Authorization: `Bearer ${token}` },
    })
      .then(async (res) => {
        if (!res.ok) throw new Error("invalid");
        const data: UserInfo = await res.json();
        if (!cancelled) {
          // /me returns UserContext (no access_token) — reuse existing token
          login(token, {
            user_id: data.user_id,
            user_code: data.user_code || "",
            user_name: data.user_name,
            role_level: data.role_level,
            dept_code: data.dept_code,
          });
        }
      })
      .catch(() => {
        if (!cancelled) logout();
      })
      .finally(() => {
        if (!cancelled) setChecking(false);
      });

    return () => { cancelled = true; };
  }, [token]); // eslint-disable-line react-hooks/exhaustive-deps

  if (!token) {
    return <Navigate to="/login" replace />;
  }

  if (checking) {
    return (
      <div className="min-h-screen bg-[#121212] flex items-center justify-center">
        <div className="flex items-center gap-2">
          <span className="w-2 h-2 bg-[#1ed760] rounded-full animate-pulse" />
          <span className="w-2 h-2 bg-[#1ed760] rounded-full animate-pulse [animation-delay:0.2s]" />
          <span className="w-2 h-2 bg-[#1ed760] rounded-full animate-pulse [animation-delay:0.4s]" />
        </div>
      </div>
    );
  }

  return <Outlet />;
}
