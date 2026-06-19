/** 登录请求体 — 对应后端 LoginRequest */
export interface LoginRequest {
  user_code: string;
  password: string;
}

/** 登录成功响应 — 对应后端 TokenResponse */
export interface TokenResponse {
  access_token: string;
  token_type: string;
  user_id: string;
  user_name: string;
  role_level: number;
  dept_code: string | null;
}

/** 前端认证用户信息 */
export interface UserInfo {
  user_id: string;
  user_code: string;
  user_name: string;
  role_level: number;
  dept_code: string | null;
}
