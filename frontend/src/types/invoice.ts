export type InvoiceStatus = 'draft' | 'sent' | 'paid' | 'overdue' | 'cancelled' | 'refunded';

export interface Client {
    id: number;
    name: string;
    email?: string;
    phone?: string;
    address?: string;
    city?: string;
    zipCode?: string;
    country?: string;
    taxId?: string;
    createdAt?: string;
    updatedAt?: string;
}

export interface InvoiceItem {
    id: number;
    description: string;
    quantity: number;
    unitPrice: number;
    taxRate: number;
    total: number;
    createdAt?: string;
    updatedAt?: string;
}

export interface Payment {
    id: number;
    amount: number;
    paymentDate: string;
    paymentMethod: string;
    reference?: string;
    notes?: string;
    createdAt?: string;
    updatedAt?: string;
}

export interface Invoice {
    id: number;
    invoiceNumber: string;
    reference?: string;
    issueDate: string;
    dueDate: string;
    status: InvoiceStatus;
    subtotal: number;
    taxAmount: number;
    totalAmount: number;
    notes?: string;
    terms?: string;
    clientId: number;
    client?: Client;
    items: InvoiceItem[];
    payments?: Payment[];
    createdAt: string;
    updatedAt: string;
    userId: number;
}

export interface InvoiceSummary {
    total: number;
    paid: number;
    pending: number;
    overdue: number;
    draft: number;
}

export interface InvoiceStats {
    totalInvoices: number;
    totalRevenue: number;
    pendingAmount: number;
    overdueAmount: number;
    monthlyStats: Array<{
        month: string;
        year: number;
        count: number;
        amount: number;
    }>;
    statusDistribution: Array<{
        status: InvoiceStatus;
        count: number;
        percentage: number;
    }>;
}

export interface PaginatedResponse<T> {
    data: T[];
    total: number;
    page: number;
    limit: number;
    totalPages: number;
    hasNextPage: boolean;
    hasPreviousPage: boolean;
    from: number;
    to: number;
}

export interface InvoiceFilters {
    status?: string;
    clientId?: string;
    startDate?: Date | null;
    endDate?: Date | null;
    amountMin?: string;
    amountMax?: string;
    search?: string;
    page?: number;
    limit?: number;
    sortBy?: string;
    sortOrder?: 'asc' | 'desc';
}
