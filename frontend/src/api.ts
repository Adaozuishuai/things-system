import axios, { AxiosError } from 'axios';
import { IntelListResponse, SearchType, TimeRange, IntelItem as IntelItemType } from './types';

// 处理 Vite 环境下 import.meta.env 可能不存在的情况
const API_BASE = (typeof import.meta !== 'undefined' && import.meta.env && import.meta.env.VITE_API_BASE_URL) || '/api';
const SSE_BASE = API_BASE;

const api = axios.create({
    baseURL: API_BASE,
});

// 响应拦截器：统一处理错误
api.interceptors.response.use(
    (response) => {
        return response;
    },
    (error: AxiosError) => {
        if (error.response) {
            const status = error.response.status;
            if (status === 401) {
                // 未授权，提示并可能跳转
                console.warn('Unauthorized (401). Please login.');
                
                // Clear local storage to ensure UI sync
                localStorage.removeItem('token');
                localStorage.removeItem('username');
                
                // 暂时使用 alert 提示，如果有了登录页可以使用 window.location.href = '/login';
                alert('登录已过期，请重新登录');
                window.location.href = '/login';
            } else if (status === 403) {
                // 禁止访问
                console.warn('Forbidden (403).');
                alert('您没有权限执行此操作');
            }
        }
        return Promise.reject(error);
    }
);

export const getIntel = async (
    type: SearchType = "all",
    q: string = "",
    range: TimeRange = "all",
    limit: number = 20,
    offset: number = 0
) => {
    const res = await api.get<IntelListResponse>('/intel/', {
        params: { type, q, range, limit, offset }
    });
    return res.data;
};

export const getIntelDetail = async (id: string) => {
    const res = await api.get<IntelItemType>(`/intel/${id}`);
    return res.data;
};

export const getFavorites = async (
    q: string = "",
    limit: number = 20,
    offset: number = 0
) => {
    const res = await api.get<IntelListResponse>('/intel/favorites', {
        params: { q, limit, offset }
    });
    return res.data;
};

export const toggleFavorite = async (id: string, favorited: boolean) => {
    const res = await api.post(`/intel/${id}/favorite`, { favorited });
    return res.data;
};

export const runAgentTask = async (query: string, type: SearchType, range: TimeRange) => {
    const res = await api.post('/agent/run', { query, type, range });
    return res.data.task_id;
};

export const getAgentStreamUrl = (taskId: string) => {
    return `${SSE_BASE}/agent/stream/${taskId}`;
};

export const getGlobalStreamUrl = (opts?: { after_ts?: number; after_id?: string }) => {
    const url = new URL(`${SSE_BASE}/agent/stream/global`, window.location.origin);
    if (opts?.after_ts !== undefined) {
        url.searchParams.set('after_ts', String(opts.after_ts));
    }
    if (opts?.after_id) {
        url.searchParams.set('after_id', opts.after_id);
    }
    return url.toString();
};

export const exportIntel = async (ids: string[], type: SearchType, range: TimeRange, q: string) => {
    const res = await api.post('/intel/export', { ids: ids.length ? ids : undefined, type, range, q }, {
        responseType: 'blob'
    });
    return res.data;
};

// Auth API
export const login = async (username: string, password: string) => {
    const res = await api.post('/auth/login', { username, password });
    return res.data;
};

export const register = async (username: string, password: string) => {
    const res = await api.post('/auth/register', { username, password });
    return res.data;
};

export const setAuthToken = (token: string | null) => {
    if (token) {
        api.defaults.headers.common['Authorization'] = `Bearer ${token}`;
    } else {
        delete api.defaults.headers.common['Authorization'];
    }
};

export const updateProfile = async (data: { username?: string, email?: string, bio?: string, preferences?: any }) => {
    const res = await api.put('/auth/me', data);
    return res.data;
};

export const changePassword = async (data: { current_password: string, new_password: string }) => {
    const res = await api.put('/auth/me/password', data);
    return res.data;
};

export const getMe = async () => {
    const res = await api.get('/auth/me');
    return res.data;
};
