import { useState, useEffect } from 'react';
import {
    Box,
    Button,
    FormControl,
    FormLabel,
    Input,
    Select,
    Textarea,
    VStack,
    HStack,
    Text,
    useToast,
    SimpleGrid,
    IconButton,
    Divider,
    NumberInput,
    NumberInputField,
    NumberInputStepper,
    NumberIncrementStepper,
    NumberDecrementStepper,
    useDisclosure,
    Modal,
    ModalOverlay,
    ModalContent,
    ModalHeader,
    ModalFooter,
    ModalBody,
    ModalCloseButton,
} from "@chakra-ui/react";

import { AddIcon, DeleteIcon } from '@chakra-ui/icons';
import { useForm, useFieldArray } from 'react-hook-form';
import { yupResolver } from '@hookform/resolvers/yup';
import * as yup from 'yup';
import { invoiceApi, companyApi } from '../services/api';

// Définir le type pour les éléments de la facture
interface InvoiceItem {
    description: string;
    quantity: number;
    unit_price: number;
    tax_rate: number;
}

// Définir le type pour les données du formulaire
type InvoiceFormData = {
    invoice_number: string;
    issue_date: string;
    due_date: string;
    company_id: number;
    items: InvoiceItem[];
    notes?: string;
};

// Validation schema
const invoiceSchema = yup.object().shape({
    invoice_number: yup.string().required('Le numéro de facture est requis'),
    issue_date: yup.string().required('La date d\'émission est requise'),
    due_date: yup.string().required('La date d\'échéance est requise'),
    company_id: yup.number().required('La société est requise'),
    items: yup.array().of(
        yup.object().shape({
            description: yup.string().required('La description est requise'),
            quantity: yup
                .number()
                .typeError('La quantité doit être un nombre')
                .positive('La quantité doit être positive')
                .required('La quantité est requise'),
            unit_price: yup
                .number()
                .typeError('Le prix unitaire doit être un nombre')
                .positive('Le prix unitaire doit être positif')
                .required('Le prix unitaire est requis'),
            tax_rate: yup
                .number()
                .typeError('Le taux de TVA doit être un nombre')
                .min(0, 'Le taux de TVA ne peut pas être négatif')
                .max(100, 'Le taux de TVA ne peut pas dépasser 100%')
                .required('Le taux de TVA est requis'),
        })
    ).min(1, 'Au moins un article est requis'),
    notes: yup.string().optional(),
});

interface InvoiceFormProps {
    onSuccess?: () => void;
    initialData?: any;
    isEditing?: boolean;
}

interface Company {
    id: number;
    name: string;
    // Add other company fields as needed
}

const InvoiceForm: React.FC<InvoiceFormProps> = ({
    onSuccess,
    initialData,
    isEditing = false,
}) => {
    const [isSubmitting, setIsSubmitting] = useState(false);
    const [companies, setCompanies] = useState<Company[]>([]);
    const [isLoadingCompanies, setIsLoadingCompanies] = useState(true);
    const { isOpen, onOpen, onClose } = useDisclosure();
    const toast = useToast();

    const {
        register,
        handleSubmit,
        control,
        formState: { errors },
        setValue,
        reset: resetForm,
        watch,
    } = useForm<InvoiceFormData>({
        resolver: yupResolver(invoiceSchema),
        defaultValues: initialData || {
            invoice_number: '',
            issue_date: new Date().toISOString().split('T')[0],
            due_date: new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
            company_id: undefined,
            items: [
                {
                    description: '',
                    quantity: 1,
                    unit_price: 0,
                    tax_rate: 19,
                },
            ],
            notes: '',
        },
    });

    const { fields, append, remove } = useFieldArray({
        control,
        name: 'items',
    });

    // Watch items to calculate totals
    const items = watch('items');
    const subtotal = items?.reduce(
        (sum: number, item: any) => sum + (item.quantity || 0) * (item.unit_price || 0),
        0
    );

    const taxTotal = items?.reduce(
        (sum: number, item: any) =>
            sum + ((item.quantity || 0) * (item.unit_price || 0) * (item.tax_rate || 0)) / 100,
        0
    );

    const total = subtotal + taxTotal;

    // Fetch companies on component mount
    useEffect(() => {
        const fetchCompanies = async () => {
            try {
                const response = await companyApi.getCompanies();
                setCompanies(response.data);
            } catch (error) {
                console.error('Error fetching companies:', error);
                toast({
                    title: 'Error',
                    description: 'Failed to load companies',
                    status: 'error',
                    duration: 5000,
                    isClosable: true,
                });
            } finally {
                setIsLoadingCompanies(false);
            }
        };

        fetchCompanies();
    }, []);

    const onSubmit = async (data: InvoiceFormData) => {
        try {
            const formData = {
                ...data,
                // S'assurer que company_id est un nombre
                company_id: Number(data.company_id),
                // Convertir les champs numériques si nécessaire
                items: data.items.map(item => ({
                    ...item,
                    quantity: Number(item.quantity),
                    unit_price: Number(item.unit_price),
                    tax_rate: Number(item.tax_rate),
                })),
            };

            if (isEditing && initialData?.id) {
                await invoiceApi.updateInvoice(initialData.id, formData);
                toast({
                    title: 'Facture mise à jour',
                    status: 'success',
                    duration: 3000,
                    isClosable: true,
                });
            } else {
                await invoiceApi.createInvoice(formData);
                toast({
                    title: 'Facture créée',
                    status: 'success',
                    duration: 3000,
                    isClosable: true,
                });
                resetForm();
            }

            onSuccess?.();
        } catch (error) {
            console.error('Error saving invoice:', error);
            toast({
                title: 'Erreur',
                description: 'Une erreur est survenue lors de la sauvegarde de la facture',
                status: 'error',
                duration: 5000,
                isClosable: true,
            });
        } finally {
            setIsSubmitting(false);
        }
    };

    const addNewItem = () => {
        append({
            description: '',
            quantity: 1,
            unit_price: 0,
            tax_rate: 19,
        });
    };

    const removeItem = (index: number) => {
        if (fields.length > 1) {
            remove(index);
        } else {
            toast({
                title: 'Error',
                description: 'At least one item is required',
                status: 'error',
                duration: 3000,
                isClosable: true,
            });
        }
    };

    const calculateLineTotal = (item: any) => {
        const quantity = parseFloat(item.quantity) || 0;
        const unitPrice = parseFloat(item.unit_price) || 0;
        const taxRate = parseFloat(item.tax_rate) || 0;
        const subtotal = quantity * unitPrice;
        const tax = (subtotal * taxRate) / 100;
        return subtotal + tax;
    };

    return (
        <Box as="form" onSubmit={handleSubmit(onSubmit)}>
            <VStack spacing={6} align="stretch">
                {/* Header Section */}
                <SimpleGrid columns={{ base: 1, md: 2 }} spacing={6}>
                    <Box>
                        <FormControl isInvalid={!!errors.invoice_number} mb={4}>
                            <FormLabel>Invoice Number *</FormLabel>
                            <Input
                                {...register('invoice_number')}
                                placeholder="e.g., INV-2023-001"
                            />
                            <Text color="red.500" fontSize="sm" mt={1}>
                                {errors.invoice_number?.message as string}
                            </Text>
                        </FormControl>

                        <FormControl isInvalid={!!errors.company_id} mb={4}>
                            <FormLabel>Company *</FormLabel>
                            <Select
                                {...register('company_id')}
                                placeholder="Select company"
                                isDisabled={isLoadingCompanies}
                            >
                                {companies.map((company) => (
                                    <option key={company.id} value={company.id}>
                                        {company.name}
                                    </option>
                                ))}
                            </Select>
                            <Text color="red.500" fontSize="sm" mt={1}>
                                {errors.company_id?.message as string}
                            </Text>
                        </FormControl>
                    </Box>

                    <Box>
                        <FormControl isInvalid={!!errors.issue_date} mb={4}>
                            <FormLabel>Issue Date *</FormLabel>
                            <Input type="date" {...register('issue_date')} />
                            <Text color="red.500" fontSize="sm" mt={1}>
                                {errors.issue_date?.message as string}
                            </Text>
                        </FormControl>

                        <FormControl isInvalid={!!errors.due_date}>
                            <FormLabel>Due Date *</FormLabel>
                            <Input type="date" {...register('due_date')} />
                            <Text color="red.500" fontSize="sm" mt={1}>
                                {errors.due_date?.message as string}
                            </Text>
                        </FormControl>
                    </Box>
                </SimpleGrid>

                {/* Items Section */}
                <Box>
                    <HStack justify="space-between" mb={4}>
                        <Text fontWeight="bold" fontSize="lg">
                            Items
                        </Text>
                        <Button
                            leftIcon={<AddIcon />}
                            colorScheme="blue"
                            size="sm"
                            onClick={addNewItem}
                        >
                            Add Item
                        </Button>
                    </HStack>

                    <VStack spacing={4} align="stretch">
                        {fields.map((field, index) => (
                            <Box
                                key={field.id}
                                borderWidth="1px"
                                borderRadius="md"
                                p={4}
                                position="relative"
                            >
                                <IconButton
                                    aria-label="Remove item"
                                    icon={<DeleteIcon />}
                                    size="sm"
                                    colorScheme="red"
                                    variant="ghost"
                                    position="absolute"
                                    top={2}
                                    right={2}
                                    onClick={() => removeItem(index)}
                                    isDisabled={fields.length <= 1}
                                />

                                <SimpleGrid columns={{ base: 1, md: 4 }} spacing={4}>
                                    <FormControl
                                        isInvalid={!!errors.items && !!errors.items[index]?.description}
                                    >
                                        <FormLabel>Description *</FormLabel>
                                        <Input
                                            {...register(`items.${index}.description` as const)}
                                            placeholder="Item description"
                                        />
                                        <Text color="red.500" fontSize="xs" mt={1}>
                                            {errors.items && errors.items[index]?.description?.message as string}
                                        </Text>
                                    </FormControl>

                                    <FormControl isInvalid={!!errors.items && !!errors.items[index]?.quantity}>
                                        <FormLabel>Quantity *</FormLabel>
                                        <NumberInput
                                            min={1}
                                            defaultValue={1}
                                            onChange={(value) =>
                                                setValue(`items.${index}.quantity`, parseFloat(value) || 0)
                                            }
                                        >
                                            <NumberInputField
                                                {...register(`items.${index}.quantity` as const, {
                                                    valueAsNumber: true,
                                                })}
                                            />
                                            <NumberInputStepper>
                                                <NumberIncrementStepper />
                                                <NumberDecrementStepper />
                                            </NumberInputStepper>
                                        </NumberInput>
                                        <Text color="red.500" fontSize="xs" mt={1}>
                                            {errors.items && errors.items[index]?.quantity?.message as string}
                                        </Text>
                                    </FormControl>

                                    <FormControl isInvalid={!!errors.items && !!errors.items[index]?.unit_price}>
                                        <FormLabel>Unit Price *</FormLabel>
                                        <NumberInput
                                            min={0}
                                            precision={2}
                                            step={0.01}
                                            onChange={(value) =>
                                                setValue(
                                                    `items.${index}.unit_price`,
                                                    parseFloat(value) || 0
                                                )
                                            }
                                        >
                                            <NumberInputField
                                                {...register(`items.${index}.unit_price` as const, {
                                                    valueAsNumber: true,
                                                })}
                                                placeholder="0.00"
                                            />
                                        </NumberInput>
                                        <Text color="red.500" fontSize="xs" mt={1}>
                                            {errors.items && errors.items[index]?.unit_price?.message as string}
                                        </Text>
                                    </FormControl>

                                    <FormControl isInvalid={!!errors.items && !!errors.items[index]?.tax_rate}>
                                        <FormLabel>Tax Rate (%) *</FormLabel>
                                        <NumberInput
                                            min={0}
                                            max={100}
                                            step={0.01}
                                            precision={2}
                                            onChange={(value) =>
                                                setValue(
                                                    `items.${index}.tax_rate`,
                                                    parseFloat(value) || 0
                                                )
                                            }
                                        >
                                            <NumberInputField
                                                {...register(`items.${index}.tax_rate` as const, {
                                                    valueAsNumber: true,
                                                })}
                                                placeholder="0"
                                            />
                                            <NumberInputStepper>
                                                <NumberIncrementStepper />
                                                <NumberDecrementStepper />
                                            </NumberInputStepper>
                                        </NumberInput>
                                        <Text color="red.500" fontSize="xs" mt={1}>
                                            {errors.items && errors.items[index]?.tax_rate?.message as string}
                                        </Text>
                                    </FormControl>
                                </SimpleGrid>

                                <Text mt={2} textAlign="right" fontWeight="medium">
                                    Line Total: ${calculateLineTotal(items?.[index] || {}).toFixed(2)}
                                </Text>
                            </Box>
                        ))}
                    </VStack>
                </Box>

                {/* Totals Section */}
                <Box ml="auto" width={{ base: '100%', md: '50%' }}>
                    <VStack align="stretch" spacing={2}>
                        <HStack justify="space-between">
                            <Text>Subtotal:</Text>
                            <Text>${subtotal.toFixed(2)}</Text>
                        </HStack>
                        <HStack justify="space-between">
                            <Text>Tax:</Text>
                            <Text>${taxTotal.toFixed(2)}</Text>
                        </HStack>
                        <Divider />
                        <HStack justify="space-between" fontSize="lg" fontWeight="bold">
                            <Text>Total:</Text>
                            <Text>${total.toFixed(2)}</Text>
                        </HStack>
                    </VStack>
                </Box>

                {/* Notes */}
                <FormControl>
                    <FormLabel>Notes</FormLabel>
                    <Textarea
                        {...register('notes')}
                        placeholder="Additional notes or terms"
                        rows={3}
                    />
                </FormControl>

                {/* Form Actions */}
                <HStack justify="flex-end" spacing={4} mt={6}>
                    <Button
                        type="button"
                        variant="outline"
                        onClick={onOpen}
                        isDisabled={isSubmitting}
                    >
                        Cancel
                    </Button>
                    <Button
                        type="submit"
                        colorScheme="blue"
                        isLoading={isSubmitting}
                        loadingText={isEditing ? 'Updating...' : 'Creating...'}
                    >
                        {isEditing ? 'Update Invoice' : 'Create Invoice'}
                    </Button>
                </HStack>
            </VStack>

            {/* Cancel Confirmation Modal */}
            <Modal isOpen={isOpen} onClose={onClose}>
                <ModalOverlay />
                <ModalContent>
                    <ModalHeader>Discard Changes?</ModalHeader>
                    <ModalCloseButton />
                    <ModalBody>
                        Are you sure you want to discard all changes? This action cannot be
                        undone.
                    </ModalBody>
                    <ModalFooter>
                        <Button variant="outline" mr={3} onClick={onClose}>
                            Cancel
                        </Button>
                        <Button
                            colorScheme="red"
                            onClick={() => {
                                onClose();
                                if (onSuccess) onSuccess();
                            }}
                        >
                            Discard
                        </Button>
                    </ModalFooter>
                </ModalContent>
            </Modal>
        </Box>
    );
};

export default InvoiceForm;
