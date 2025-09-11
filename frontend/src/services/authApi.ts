import api from './api';

interface LoginCredentials {
    email: string;
    password: string;
}

interface LoginResponse {
    token: string;
    user: {
        id: number;
        email: string;
        name: string;
        role: string;
    };
}

export const authApi = {
    // Login user
    login: (credentials: LoginCredentials): Promise<{ data: LoginResponse }> =>
        api.post('/auth/login', credentials),

    // Logout user
    logout: (): Promise<void> =>
        api.post('/auth/logout'),

    // Get current user profile
    getMe: (): Promise<{ data: any }> =>
        api.get('/auth/me'),

    // Refresh access token
    refreshToken: (): Promise<{ data: { token: string } }> =>
        api.post('/auth/refresh-token'),

    // Register new user (optional)
    register: (userData: {
        name: string;
        email: string;
        password: string;
        role?: string;
    }): Promise<{ data: any }> =>
        api.post('/auth/register', userData),

    // Request password reset
    forgotPassword: (email: string): Promise<void> =>
        api.post('/auth/forgot-password', { email }),

    // Reset password with token
    resetPassword: (token: string, newPassword: string): Promise<void> =>
        api.post(`/auth/reset-password/${token}`, { password: newPassword }),

    // Update user profile
    updateProfile: (data: {
        name?: string;
        email?: string;
        currentPassword?: string;
        newPassword?: string;
    }): Promise<{ data: any }> =>
        api.put('/auth/me', data),
};
