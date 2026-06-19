import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { useAuthStore } from "../../stores/authStore";
import type { TokenResponse } from "../../types/auth";

function GridPattern() {
  return (
    <div
      className="absolute inset-0 opacity-[0.03] pointer-events-none"
      style={{
        backgroundImage:
          "linear-gradient(rgba(255,255,255,0.05) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.05) 1px, transparent 1px)",
        backgroundSize: "60px 60px",
        maskImage: "radial-gradient(ellipse 80% 60% at 50% 40%, black 30%, transparent 70%)",
        WebkitMaskImage: "radial-gradient(ellipse 80% 60% at 50% 40%, black 30%, transparent 70%)",
      }}
    />
  );
}

function AmbientGlow() {
  return (
    <>
      <div
        className="absolute rounded-full blur-[120px] opacity-[0.06] pointer-events-none"
        style={{
          width: "600px",
          height: "600px",
          background: "radial-gradient(circle, #1ed760 0%, transparent 70%)",
          top: "50%",
          left: "50%",
          transform: "translate(-50%, -60%)",
        }}
      />
      <div
        className="absolute rounded-full blur-[100px] opacity-[0.04] pointer-events-none"
        style={{
          width: "400px",
          height: "400px",
          background: "radial-gradient(circle, #539df5 0%, transparent 70%)",
          bottom: "10%",
          right: "15%",
        }}
      />
    </>
  );
}

export function LoginPage() {
  const [userCode, setUserCode] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [mounted, setMounted] = useState(false);
  const navigate = useNavigate();
  const login = useAuthStore((s) => s.login);

  useEffect(() => {
    const t = requestAnimationFrame(() => setMounted(true));
    return () => cancelAnimationFrame(t);
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);

    try {
      const res = await fetch("/api/v1/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ user_code: userCode.trim(), password }),
      });

      if (!res.ok) {
        const detail = await res.json().catch(() => ({}));
        setError(detail.detail || "登录失败，请检查工号和密码");
        return;
      }

      const data: TokenResponse = await res.json();
      login(data.access_token, {
        user_id: data.user_id,
        user_code: userCode.trim(),
        user_name: data.user_name,
        role_level: data.role_level,
        dept_code: data.dept_code,
      });
      navigate("/", { replace: true });
    } catch {
      setError("网络错误，请重试");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="relative min-h-screen bg-bg-deepest flex items-center justify-center overflow-hidden">
      {/* Background atmosphere */}
      <AmbientGlow />
      <GridPattern />

      {/* Content */}
      <div
        className={`relative z-10 w-full max-w-[380px] px-6 transition-all duration-1000 ease-[cubic-bezier(0.16,1,0.3,1)] ${
          mounted ? "opacity-100 translate-y-0" : "opacity-0 translate-y-4"
        }`}
      >
        {/* Brand mark */}
        <div
          className="text-center mb-10 transition-all duration-1000 delay-100 ease-[cubic-bezier(0.16,1,0.3,1)]"
          style={{
            opacity: mounted ? 1 : 0,
            transform: mounted ? "translateY(0)" : "translateY(8px)",
          }}
        >
          {/* Logo mark */}
          <div className="inline-flex items-center justify-center w-12 h-12 rounded-2xl bg-[#1ed760] mb-5 shadow-[0_0_40px_-8px_rgba(30,215,96,0.3)]">
            <svg
              width="22"
              height="22"
              viewBox="0 0 24 24"
              fill="none"
              stroke="#121212"
              strokeWidth="2.5"
              strokeLinecap="round"
              strokeLinejoin="round"
            >
              <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
              <path d="M8 10h.01M12 10h.01M16 10h.01" />
            </svg>
          </div>

          <h1
            className="text-[28px] font-bold text-white tracking-[-0.02em]"
            style={{ fontFamily: "'Inter', system-ui, sans-serif" }}
          >
            SkillCloud<wbr />HS
          </h1>

          <div className="flex items-center justify-center gap-2 mt-3">
            <span className="w-5 h-px bg-[#333]" />
            <p className="text-text-subdued text-[13px] tracking-[0.05em] uppercase">
              AI 数据问答系统
            </p>
            <span className="w-5 h-px bg-[#333]" />
          </div>
        </div>

        {/* Card */}
        <form
          onSubmit={handleSubmit}
          className="relative bg-bg-card rounded-2xl p-7 space-y-5
                     shadow-[0_0_0_1px_rgba(255,255,255,0.04),0_8px_32px_-8px_rgba(0,0,0,0.6)]
                     transition-all duration-1000 delay-200 ease-[cubic-bezier(0.16,1,0.3,1)]"
          style={{
            opacity: mounted ? 1 : 0,
            transform: mounted ? "translateY(0)" : "translateY(12px)",
          }}
        >
          {/* Subtle top accent line */}
          <div className="absolute top-0 left-6 right-6 h-px bg-gradient-to-r from-transparent via-[#1ed760]/30 to-transparent" />

          {/* 工号 */}
          <div className="space-y-2">
            <div className="relative">
              <input
                id="user_code"
                type="text"
                value={userCode}
                onChange={(e) => setUserCode(e.target.value)}
                placeholder="请输入工号"
                autoFocus
                required
                className="w-full bg-bg-deepest text-white rounded-xl px-4 py-3 text-sm
                           shadow-[inset_0_1px_0_0_rgba(255,255,255,0.02),0_0_0_1px_rgba(255,255,255,0.06)]
                           focus:outline-none focus:shadow-[inset_0_1px_0_0_rgba(30,215,96,0.08),0_0_0_2px_rgba(30,215,96,0.25)]
                           placeholder:text-text-subdued transition-shadow duration-300"
              />
            </div>
          </div>

          {/* 密码 */}
          <div className="space-y-2">

            <div className="relative">
              <input
                id="password"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="请输入密码"
                required
                className="w-full bg-bg-deepest text-white rounded-xl px-4 py-3 text-sm
                           shadow-[inset_0_1px_0_0_rgba(255,255,255,0.02),0_0_0_1px_rgba(255,255,255,0.06)]
                           focus:outline-none focus:shadow-[inset_0_1px_0_0_rgba(30,215,96,0.08),0_0_0_2px_rgba(30,215,96,0.25)]
                           placeholder:text-text-subdued transition-shadow duration-300"
              />
            </div>
          </div>

          {/* 错误提示 */}
          <div
            className={`grid transition-all duration-300 ease-out ${
              error ? "grid-rows-[1fr] opacity-100" : "grid-rows-[0fr] opacity-0"
            }`}
          >
            <div className="overflow-hidden">
              <p className="text-error text-xs text-center py-1">{error}</p>
            </div>
          </div>

          {/* 登录按钮 */}
          <button
            type="submit"
            disabled={loading || !userCode.trim() || !password}
            className="relative w-full bg-[#1ed760] text-black font-bold text-sm
                       rounded-xl py-3 tracking-[0.02em]
                       hover:bg-[#1fdf64] hover:shadow-[0_0_32px_-4px_rgba(30,215,96,0.35)]
                       disabled:opacity-30 disabled:hover:shadow-none disabled:cursor-not-allowed
                       transition-all duration-300 ease-out cursor-pointer
                       overflow-hidden group"
          >
            {/* Shine effect on hover */}
            <span className="absolute inset-0 bg-gradient-to-r from-transparent via-white/15 to-transparent -translate-x-full group-hover:translate-x-full transition-transform duration-700 ease-out pointer-events-none" />
            <span className="relative">
              {loading ? (
                <span className="inline-flex items-center gap-2">
                  <span className="w-2 h-2 bg-black/40 rounded-full animate-pulse" />
                  <span className="w-2 h-2 bg-black/40 rounded-full animate-pulse [animation-delay:0.15s]" />
                  <span className="w-2 h-2 bg-black/40 rounded-full animate-pulse [animation-delay:0.3s]" />
                </span>
              ) : (
                "登  录"
              )}
            </span>
          </button>
        </form>

        {/* Footer */}
        <p
          className="text-center text-text-subdued text-[11px] mt-8 transition-all duration-1000 delay-300"
          style={{
            opacity: mounted ? 0.5 : 0,
            transform: mounted ? "translateY(0)" : "translateY(4px)",
          }}
        >
          SkillCloudHS v0.1.0
        </p>
      </div>
    </div>
  );
}
