import { api } from './api';
import { saveAs } from 'file-saver';
import { format } from 'date-fns';

const TEIF_API_BASE = '/teif';

export const teifService = {
    /**
     * Generate TEIF XML for an invoice
     * @param invoiceId - The ID of the invoice to generate TEIF for
     * @returns The generated XML as a string
     */
    generateTeif: async (invoiceId: number): Promise<string> => {
        const response = await api.get(`${TEIF_API_BASE}/invoices/${invoiceId}/generate`, {
            responseType: 'text',
            headers: {
                'Accept': 'application/xml',
            },
        });
        return response.data;
    },

    /**
     * Download TEIF XML file for an invoice
     * @param invoiceId - The ID of the invoice to download
     * @param fileName - Optional custom file name
     */
    downloadTeif: async (invoiceId: number, fileName?: string): Promise<void> => {
        const xml = await this.generateTeif(invoiceId);
        const blob = new Blob([xml], { type: 'application/xml' });

        // Generate file name if not provided
        const defaultName = `facture_${format(new Date(), 'yyyyMMdd')}_${invoiceId}.xml`;
        saveAs(blob, fileName || defaultName);
    },

    /**
     * Upload and process a PDF invoice
     * @param file - The PDF file to process
     * @returns The processed invoice data
     */
    uploadPdfInvoice: async (file: File) => {
        const formData = new FormData();
        formData.append('file', file);

        const response = await api.post(`${TEIF_API_BASE}/invoices/upload-pdf`, formData, {
            headers: {
                'Content-Type': 'multipart/form-data',
            },
        });

        return response.data;
    },

    /**
     * Get TEIF XML schema validation for an invoice
     * @param invoiceId - The ID of the invoice to validate
     * @returns Validation results
     */
    validateTeif: async (invoiceId: number) => {
        const response = await api.get(`${TEIF_API_BASE}/invoices/${invoiceId}/validate`);
        return response.data;
    },

    /**
     * Get the TEIF XML schema
     * @returns The TEIF XML schema as a string
     */
    getTeifSchema: async (): Promise<string> => {
        const response = await api.get(`${TEIF_API_BASE}/schema`, {
            responseType: 'text',
            headers: {
                'Accept': 'application/xml',
            },
        });
        return response.data;
    },

    /**
     * Get TEIF version information
     * @returns TEIF version details
     */
    getTeifVersion: async () => {
        const response = await api.get(`${TEIF_API_BASE}/version`);
        return response.data;
    },

    /**
     * Sign TEIF XML with digital signature
     * @param invoiceId - The ID of the invoice to sign
     * @param certificateId - The ID of the certificate to use for signing
     * @returns The signed XML as a string
     */
    signTeif: async (invoiceId: number, certificateId: string): Promise<string> => {
        const response = await api.post(
            `${TEIF_API_BASE}/invoices/${invoiceId}/sign`,
            { certificateId },
            {
                responseType: 'text',
                headers: {
                    'Accept': 'application/xml',
                },
            }
        );
        return response.data;
    },

    /**
     * Verify TEIF XML signature
     * @param invoiceId - The ID of the invoice to verify
     * @returns Verification results
     */
    verifyTeifSignature: async (invoiceId: number) => {
        const response = await api.get(`${TEIF_API_BASE}/invoices/${invoiceId}/verify`);
        return response.data;
    },

    /**
     * Get TEIF generation status for an invoice
     * @param invoiceId - The ID of the invoice to check
     * @returns Generation status
     */
    getTeifStatus: async (invoiceId: number) => {
        const response = await api.get(`${TEIF_API_BASE}/invoices/${invoiceId}/status`);
        return response.data;
    },

    /**
     * Get TEIF generation history for an invoice
     * @param invoiceId - The ID of the invoice
     * @returns Array of generation history entries
     */
    getTeifHistory: async (invoiceId: number) => {
        const response = await api.get(`${TEIF_API_BASE}/invoices/${invoiceId}/history`);
        return response.data;
    },

    /**
     * Preview TEIF XML in the browser
     * @param invoiceId - The ID of the invoice to preview
     * @returns A blob URL for the XML preview
     */
    previewTeif: async (invoiceId: number): Promise<string> => {
        const xml = await this.generateTeif(invoiceId);
        const blob = new Blob([xml], { type: 'application/xml' });
        return URL.createObjectURL(blob);
    },

    /**
     * Clean up a preview URL
     * @param url - The URL to revoke
     */
    revokePreviewUrl: (url: string): void => {
        if (url.startsWith('blob:')) {
            URL.revokeObjectURL(url);
        }
    },
};
