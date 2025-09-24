import axios, { type AxiosResponse, type InternalAxiosRequestConfig, type AxiosError } from 'axios';
import type { Invoice } from '../types/invoice';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

// Define types for common API responses
interface ApiResponse<T> {
    data: T;
    message?: string;
    status: string;
}

interface PaginatedResponse<T> {
    data: T[];  // Changé de 'items' à 'data'
    total: number;
    page: number;
    limit: number;
    totalPages: number;
    hasNextPage?: boolean;
    hasPreviousPage?: boolean;
    from?: number;
    to?: number;
}

interface ErrorResponse {
    message: string;
    statusCode: number;
    error?: string;
}

// Create axios instance with base URL and default headers
const api = axios.create({
    baseURL: API_URL,
    headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
    },
    timeout: 30000, // 30 seconds timeout
});

// Request interceptor
api.interceptors.request.use(
    (config: InternalAxiosRequestConfig) => {
        // Add any custom request headers here if needed
        return config;
    },
    (error) => {
        return Promise.reject(error);
    }
);

// Response interceptor for handling common errors
api.interceptors.response.use(
    (response: AxiosResponse) => response,
    (error: AxiosError<ErrorResponse>) => {
        if (error.response) {
            // The request was made and the server responded with a status code
            const errorMessage = error.response.data?.message || 'An error occurred';
            console.error('API Error:', {
                status: error.response.status,
                message: errorMessage,
                url: error.config?.url,
                data: error.response.data,
            });
            
            // Create a more specific error message
            const errorWithDetails = new Error(errorMessage) as Error & {
                status?: number;
                code?: string;
                response?: any;
            };
            errorWithDetails.status = error.response.status;
            errorWithDetails.code = error.code;
            errorWithDetails.response = error.response.data;
            
            return Promise.reject(errorWithDetails);
        } else if (error.request) {
            // The request was made but no response was received
            console.error('No response received:', error.request);
            return Promise.reject(new Error('No response received from server. Please check your connection.'));
        } else {
            // Something happened in setting up the request
            console.error('Request setup error:', error.message);
            return Promise.reject(new Error('Error setting up request. Please try again.'));
        }
    }
);

// Update the handleResponse function
const handleResponse = <T>(response: AxiosResponse<ApiResponse<T>>): T => {
    if (!response.data) {
        throw new Error('No data received from server');
    }
    // Check if the response status is 'success'
    if (response.data.status !== 'success') {
        throw new Error(response.data.message || 'Request failed');
    }
    return response.data.data;
};

// Dashboard API
export const dashboardApi = {
    // Get dashboard statistics
    getDashboardStats: async (): Promise<any> => {
        try {
            const response = await api.get<ApiResponse<any>>('/dashboard/stats');
            return handleResponse(response);
        } catch (error) {
            console.error('Error in getDashboardStats:', error);
            // Return mock data if the endpoint is not available
            if ((error as any).status === 404) {
                return {
                    totals: {
                        invoices: 0,
                        companies: 0,
                        revenue: 0,
                        tax: 0,
                        net: 0,
                    },
                    status: {
                        draft: 0,
                        sent: 0,
                        paid: 0,
                        overdue: 0,
                        cancelled: 0,
                    }
                };
            }
            throw error;
        }
    },

    // Get monthly statistics
    getMonthlyStats: async (params: { months: number }): Promise<any[]> => {
        try {
            const response = await api.get<ApiResponse<any[]>>('/dashboard/monthly-stats', { params });
            return handleResponse(response);
        } catch (error) {
            console.error('Error in getMonthlyStats:', error);
            // Return mock data if the endpoint is not available
            if ((error as any).status === 404) {
                return Array.from({ length: params.months || 6 }, (_, i) => {
                    const date = new Date();
                    date.setMonth(date.getMonth() - i);
                    return {
                        month: date.toISOString().split('T')[0],
                        invoice_count: 0,
                        total_amount: 0,
                        tax_amount: 0,
                    };
                }).reverse();
            }
            throw error;
        }
    },
};

// Invoices API
export const invoiceApi = {
  // Dans invoiceApi.ts
getInvoices: async (params?: any): Promise<any> => {
    const response = await api.get('/invoices', { params });
    return response.data; // Retourne directement les données de la réponse
},

    // Get a single invoice by ID
    getInvoice: async (id: number): Promise<any> => {
        const response = await api.get<ApiResponse<any>>(`/invoices/${id}`);
        return handleResponse(response);
    },

    // Create a new invoice
    createInvoice: async (data: FormData): Promise<any> => {
        const response = await api.post<ApiResponse<any>>('/invoices/', data, {
            headers: {
                'Content-Type': 'multipart/form-data',
            },
        });
        return handleResponse(response);
    },

    // Update an existing invoice
    updateInvoice: async (id: number, data: FormData): Promise<any> => {
        const response = await api.put<ApiResponse<any>>(`/invoices/${id}`, data, {
            headers: {
                'Content-Type': 'multipart/form-data',
            },
        });
        return handleResponse(response);
    },

    // Delete an invoice
    deleteInvoice: async (id: number): Promise<void> => {
        await api.delete<ApiResponse<void>>(`/invoices/${id}`);
    },

    // Download invoice as PDF
    downloadPdf: async (id: number): Promise<Blob> => {
        const response = await api.get(`/invoices/${id}/download`, { 
            responseType: 'blob' 
        });
        return response.data;
    },

    // Send invoice via email
    sendEmail: async (
        id: number, 
        emailData: { 
            to: string; 
            subject?: string; 
            message?: string;
            cc?: string[];
            bcc?: string[];
        }
    ): Promise<{ success: boolean; message: string }> => {
        const response = await api.post<ApiResponse<{ 
            success: boolean; 
            message: string 
        }>>(
            `/invoices/${id}/send-email`,
            emailData
        );
        return handleResponse(response);
    },
};

// Companies API
export const companyApi = {
    // Get all companies
    getCompanies: async (params?: { 
        search?: string; 
        page?: number; 
        limit?: number;
        sort_by?: string;
        sort_order?: 'asc' | 'desc';
    }): Promise<PaginatedResponse<any>> => {
        const response = await api.get<ApiResponse<PaginatedResponse<any>>>('/companies/', { params });
        return handleResponse(response);
    },

    // Get a single company by ID
    getCompany: async (id: number): Promise<any> => {
        const response = await api.get<ApiResponse<any>>(`/companies/${id}`);
        return handleResponse(response);
    },

    // Create a new company
    createCompany: async (data: any): Promise<any> => {
        const response = await api.post<ApiResponse<any>>('/companies/', data);
        return handleResponse(response);
    },

    // Update an existing company
    updateCompany: async (id: number, data: any): Promise<any> => {
        const response = await api.put<ApiResponse<any>>(`/companies/${id}`, data);
        return handleResponse(response);
    },

    // Delete a company
    deleteCompany: async (id: number): Promise<void> => {
        await api.delete<ApiResponse<void>>(`/companies/${id}`);
    },

    // Search companies by name or tax ID
    searchCompanies: async (query: string): Promise<any[]> => {
        const response = await api.get<ApiResponse<any[]>>('/companies/search', {
            params: { q: query }
        });
        return handleResponse(response);
    }
};

// Export the axios instance for direct use if needed
export default api;