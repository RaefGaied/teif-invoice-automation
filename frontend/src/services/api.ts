import axios, { AxiosError, type AxiosResponse, type InternalAxiosRequestConfig } from 'axios';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

// Create axios instance with base URL and default headers
const api = axios.create({
    baseURL: API_URL,
    headers: {
        'Content-Type': 'application/json',
    },
    withCredentials: true,
});

// Request interceptor for adding auth token
api.interceptors.request.use(
    (config: InternalAxiosRequestConfig) => {
        const token = localStorage.getItem('auth_token');
        if (token) {
            config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
    },
    (error) => {
        return Promise.reject(error);
    }
);

// Response interceptor for handling common errors
api.interceptors.response.use(
    (response: AxiosResponse) => response,
    (error: AxiosError) => {
        if (error.response?.status === 401) {
            // Handle unauthorized access
            localStorage.removeItem('auth_token');
            window.location.href = '/login';
        }
        return Promise.reject(error);
    }
);

// Invoices API
export const invoiceApi = {
    // Get all invoices with optional filters
    getInvoices: (params?: {
        status?: string;
        start_date?: string;
        end_date?: string;
        company_id?: number;
        page?: number;
        limit?: number;
    }) => api.get('/invoices/', { params }),

    // Get a single invoice by ID
    getInvoice: (id: number) => api.get(`/invoices/${id}`),

    // Create a new invoice
    createInvoice: (data: FormData) =>
        api.post('/invoices/', data, {
            headers: {
                'Content-Type': 'multipart/form-data',
            },
        }),

    // Update an existing invoice
    updateInvoice: (id: number, data: FormData) =>
        api.put(`/invoices/${id}`, data, {
            headers: {
                'Content-Type': 'multipart/form-data',
            },
        }),

    // Delete an invoice
    deleteInvoice: (id: number) => api.delete(`/invoices/${id}`),

    // Download invoice as PDF
    downloadPdf: (id: number) =>
        api.get(`/invoices/${id}/download`, { responseType: 'blob' }),

    // Send invoice via email
    sendEmail: (id: number, emailData: { to: string; subject?: string; message?: string }) =>
        api.post(`/invoices/${id}/send-email`, emailData),

    // Dashboard endpoints
    getDashboardStats: () => api.get('/dashboard/stats'),
    getMonthlyStats: (params: { months: number }) =>
        api.get('/dashboard/monthly-stats', { params }),
};

// Companies API
export const companyApi = {
    // Get all companies
    getCompanies: (params?: { search?: string; page?: number; limit?: number }) =>
        api.get('/companies/', { params }),

    // Get a single company by ID
    getCompany: (id: number) => api.get(`/companies/${id}`),

    // Create a new company
    createCompany: (data: any) => api.post('/companies/', data),

    // Update an existing company
    updateCompany: (id: number, data: any) => api.put(`/companies/${id}`, data),

    // Delete a company
    deleteCompany: (id: number) => api.delete(`/companies/${id}`),
};

// Auth API
export const authApi = {
    // User login
    login: (credentials: { email: string; password: string }) =>
        api.post('/auth/login', credentials),

    // User logout
    logout: () => api.post('/auth/logout'),

    // Get current user
    getCurrentUser: () => api.get('/auth/me'),

    // Refresh token
    refreshToken: () => api.post('/auth/refresh-token'),
};

export default api;
