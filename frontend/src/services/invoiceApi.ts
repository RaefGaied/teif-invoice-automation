import type { AxiosResponse } from 'axios';
import type { Invoice, InvoiceFilters, InvoiceStats, PaginatedResponse } from '../types/invoice';
import api from './api';
import axios from 'axios';

const INVOICE_API_BASE = '/invoices';

interface GetInvoicesParams {
    page?: number;
    limit?: number;
    search?: string;
    status?: string;
    clientId?: string;
    startDate?: Date | null;
    endDate?: Date | null;
    amountMin?: string;
    amountMax?: string;
    sortBy?: string;
    sortOrder?: 'asc' | 'desc';
}


interface ApiResponse<T> {
    data: T;
    message?: string;
}

export const invoiceApi = {
    /**
     * Get paginated list of invoices with optional filters
     */
    getInvoices: async (params: GetInvoicesParams = {}): Promise<PaginatedResponse<Invoice>> => {
        const queryParams: Record<string, unknown> = {
            page: params.page || 1,
            limit: params.limit || 10,
        };

        // Add optional filters
        if (params.search) queryParams.search = params.search;
        if (params.status) queryParams.status = params.status;
        if (params.clientId) queryParams.clientId = params.clientId;
        if (params.startDate) queryParams.startDate = params.startDate.toISOString().split('T')[0];
        if (params.endDate) queryParams.endDate = params.endDate.toISOString().split('T')[0];
        if (params.amountMin) queryParams.amountMin = params.amountMin;
        if (params.amountMax) queryParams.amountMax = params.amountMax;
        if (params.sortBy) queryParams.sortBy = params.sortBy;
        if (params.sortOrder) queryParams.sortOrder = params.sortOrder;

        const response = await api.get<ApiResponse<PaginatedResponse<Invoice>>>(INVOICE_API_BASE, { 
            params: queryParams 
        });
        return response.data.data;
    },

    /**
     * Get a single invoice by ID
     */
    getInvoiceById: async (id: number): Promise<Invoice> => {
        const response = await api.get<ApiResponse<Invoice>>(`${INVOICE_API_BASE}/${id}`);
        return response.data.data;
    },

    /**
     * Create a new invoice
     */
    createInvoice: async (invoiceData: Partial<Invoice>): Promise<Invoice> => {
        const response = await api.post<ApiResponse<Invoice>>(INVOICE_API_BASE, invoiceData);
        return response.data.data;
    },

    /**
     * Update an existing invoice
     */
    updateInvoice: async (id: number, invoiceData: Partial<Invoice>): Promise<Invoice> => {
        const response = await api.put<ApiResponse<Invoice>>(
            `${INVOICE_API_BASE}/${id}`, 
            invoiceData
        );
        return response.data.data;
    },

    /**
     * Delete an invoice
     */
    deleteInvoice: async (id: number): Promise<void> => {
        await api.delete(`${INVOICE_API_BASE}/${id}`);
    },

    /**
     * Send an invoice to the client
     */
    sendInvoice: async (id: number): Promise<{ message: string }> => {
        const response = await api.post<ApiResponse<{ message: string }>>(
            `${INVOICE_API_BASE}/${id}/send`
        );
        return response.data.data;
    },

    /**
     * Mark an invoice as paid
     */
    markAsPaid: async (
        id: number, 
        paymentData: { amount: number; paymentDate: string; paymentMethod: string }
    ): Promise<Invoice> => {
        const response = await api.post<ApiResponse<Invoice>>(
            `${INVOICE_API_BASE}/${id}/pay`, 
            paymentData
        );
        return response.data.data;
    },

    /**
     * Download invoice as PDF
     */
    downloadPdf: async (id: number): Promise<Blob> => {
        const response = await api.get(`${INVOICE_API_BASE}/${id}/download`, {
            responseType: 'blob',
        });
        return response.data;
    },

    /**
     * Get invoice statistics
     */
    getStats: async (): Promise<InvoiceStats> => {
        const response = await api.get<ApiResponse<InvoiceStats>>(`${INVOICE_API_BASE}/stats`);
        return response.data.data;
    },

    /**
     * Get next available invoice number
     */
    getNextInvoiceNumber: async (): Promise<{ nextNumber: string }> => {
        const response = await api.get<ApiResponse<{ nextNumber: string }>>(
            `${INVOICE_API_BASE}/next-number`
        );
        return response.data.data;
    },

    /**
     * Generate TEIF XML for an invoice
     */
    generateTeif: async (id: number): Promise<{ xml: string }> => {
        const response = await api.get<ApiResponse<{ xml: string }>>(
            `${INVOICE_API_BASE}/${id}/generate-teif`
        );
        return response.data.data;
    },

    /**
     * Upload and process a PDF invoice
     */
    uploadPdf: async (file: File): Promise<{ invoice: Invoice; message: string }> => {
        const formData = new FormData();
        formData.append('file', file);

        const response = await api.post<ApiResponse<{ invoice: Invoice; message: string }>>(
            `${INVOICE_API_BASE}/upload-pdf`,
            formData,
            {
                headers: {
                    'Content-Type': 'multipart/form-data',
                },
            }
        );

        return response.data.data;
    },

    /**
     * Export invoices to Excel
     */
    exportToExcel: async (filters: Partial<InvoiceFilters> = {}): Promise<Blob> => {
        const queryParams: Record<string, unknown> = {};

        // Add filters if provided
        if (filters.status) queryParams.status = filters.status;
        if (filters.clientId) queryParams.clientId = filters.clientId;
        if (filters.startDate) queryParams.startDate = filters.startDate.toISOString().split('T')[0];
        if (filters.endDate) queryParams.endDate = filters.endDate.toISOString().split('T')[0];
        if (filters.amountMin) queryParams.amountMin = filters.amountMin;
        if (filters.amountMax) queryParams.amountMax = filters.amountMax;

        const response = await api.get(`${INVOICE_API_BASE}/export`, {
            params: queryParams,
            responseType: 'blob',
        });

        return response.data;
    },

    /**
     * Get recent activity for invoices
     */
    getRecentActivity: async (limit: number = 10): Promise<Array<{
        id: number;
        action: string;
        description: string;
        date: string;
        userId: number;
        userName: string;
        invoiceId: number;
        invoiceNumber: string;
    }>> => {
        const response = await api.get<ApiResponse<Array<{
            id: number;
            action: string;
            description: string;
            date: string;
            userId: number;
            userName: string;
            invoiceId: number;
            invoiceNumber: string;
        }>>>(
            `${INVOICE_API_BASE}/recent-activity`,
            { params: { limit } }
        );
        return response.data.data;
    },

    /**
     * Validate invoice data before submission
     */
    validateInvoice: async (
        invoiceData: Partial<Invoice>
    ): Promise<{ valid: boolean; errors: Record<string, string[]> }> => {
        try {
            await api.post(`${INVOICE_API_BASE}/validate`, invoiceData);
            return { valid: true, errors: {} };
        } catch (error) {
            if (axios.isAxiosError(error) && error.response?.status === 422) {
                return { 
                    valid: false, 
                    errors: error.response.data.errors || {} 
                };
            }
            throw error;
        }
    },

    /**
     * Duplicate an existing invoice
     */
    duplicateInvoice: async (id: number): Promise<Invoice> => {
        const response = await api.post<ApiResponse<Invoice>>(
            `${INVOICE_API_BASE}/${id}/duplicate`
        );
        return response.data.data;
    },
};