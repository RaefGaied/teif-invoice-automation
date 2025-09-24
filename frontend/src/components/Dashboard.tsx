import React, { useEffect, useState, useCallback } from 'react';
import {
    Box,
    SimpleGrid,
    Text,
    useColorModeValue,
    Heading,
    Flex,
    Icon,
    HStack,
    Spinner,
    Button,
    useToast,
    StatArrow,
    Stat,
    StatHelpText,
} from '@chakra-ui/react';
import {
    FiDollarSign,
    FiFileText,
    FiAlertCircle,
    FiRefreshCw,
    FiUsers
} from 'react-icons/fi';
import {
    LineChart,
    Line,
    BarChart,
    Bar,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    Legend,
    ResponsiveContainer,
    type TooltipProps,

} from 'recharts';
import api, { dashboardApi } from '../services/api';
import { format } from 'date-fns';

// Mock data for when API is not available
const mockDashboardStats = {
    status: 'success',
    data: {
        totals: {
            invoices: 42,
            companies: 15,
            revenue: 125000,
            tax: 25000,
            net: 100000,
        },
        status: {
            draft: 5,
            sent: 12,
            paid: 20,
            overdue: 3,
            cancelled: 2,
        }
    }
};

const generateMockMonthlyData = (months: number): MonthlyData[] => {
    const now = new Date();
    return Array.from({ length: months }, (_, i) => {
        const date = new Date(now);
        date.setMonth(now.getMonth() - i);
        const monthData: MonthlyData = {
            month: date.toISOString().split('T')[0].slice(0, 7),
            invoice_count: Math.floor(Math.random() * 20) + 5,
            total_amount: Math.floor(Math.random() * 50000) + 10000,
            tax_amount: 0
        };
        monthData.tax_amount = Math.round(monthData.total_amount * 0.18);
        return monthData;
    }).reverse();
};

interface CustomTooltipProps extends TooltipProps<number, string> {
    active?: boolean;
    payload?: {
        value: number;
        name: string;
        dataKey: string;
        color: string;
    }[];
    label?: string;
}

interface DashboardStats {
    status: string;
    data: {
        totals: {
            invoices: number;
            companies: number;
            revenue: number;
            tax: number;
            net: number;
        };
        status: Record<string, number>;
    };
}
interface MonthlyData {
    month: string;
    invoice_count: number;
    total_amount: number;
    tax_amount: number;
}

// Format currency helper function
const formatCurrency = (amount: number): string => {
    return new Intl.NumberFormat('fr-TN', {
        style: 'currency',
        currency: 'TND',
        minimumFractionDigits: 3,
        maximumFractionDigits: 3,
    }).format(amount);
};

const CustomTooltip = ({ active, payload, label }: CustomTooltipProps) => {
    const cardBg = useColorModeValue('white', 'gray.800');
    if (active && payload && payload.length) {
        return (
            <Box bg={cardBg} p={3} borderRadius="md" borderWidth="1px" boxShadow="lg">
                <Text fontWeight="bold" mb={2}>{label}</Text>
                {payload.map((entry, index: number) => (
                    <Text key={`tooltip-${index}`} style={{ color: entry.color }}>
                        {entry.name}: {entry.name.toLowerCase().includes('amount')
                            ? formatCurrency(Number(entry.value))
                            : entry.value}
                    </Text>
                ))}
            </Box>
        );
    }
    return null;
};

const Dashboard: React.FC = () => {
    const [stats, setStats] = useState<DashboardStats | null>(null);
    const [monthlyData, setMonthlyData] = useState<MonthlyData[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    const [isRefreshing, setIsRefreshing] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const toast = useToast();
    const cardBg = useColorModeValue('white', 'gray.800');
    const borderColor = useColorModeValue('gray.200', 'gray.700');
    const textColor = useColorModeValue('gray.800', 'white');

    const fetchDashboardData = useCallback(async (isRefresh = false) => {
        const loadingState = isRefresh ? setIsRefreshing : setIsLoading;
        try {
            loadingState(true);
            setError(null);

            try {
                // Try to fetch from API first
                const [statsResponse, monthlyResponse] = await Promise.allSettled([
                    dashboardApi.getDashboardStats().catch(() => null),
                    dashboardApi.getMonthlyStats({ months: 6 }).catch(() => null)
                ]);

                // Use API data if available, otherwise fall back to mock data
                const statsData = statsResponse.status === 'fulfilled' && statsResponse.value?.status === 'success'
                    ? statsResponse.value
                    : mockDashboardStats;

                const monthlyData = monthlyResponse.status === 'fulfilled' && Array.isArray(monthlyResponse.value)
                    ? monthlyResponse.value
                    : generateMockMonthlyData(6);

                setStats(statsData);
                setMonthlyData(monthlyData);

                // If both API calls failed, show a warning but continue with mock data
                if ((statsResponse.status === 'rejected' || !statsResponse.value) ||
                    (monthlyResponse.status === 'rejected' || !monthlyResponse.value)) {
                    toast({
                        title: 'Info',
                        description: 'Using demo data. Some features may be limited.',
                        status: 'info',
                        duration: 5000,
                        isClosable: true,
                    });
                }
            } catch (apiError) {
                console.error('Error in API calls:', apiError);
                // Use mock data as fallback
                setStats(mockDashboardStats);
                setMonthlyData(generateMockMonthlyData(6));

                toast({
                    title: 'Info',
                    description: 'Using demo data. Some features may be limited.',
                    status: 'info',
                    duration: 5000,
                    isClosable: true,
                });
            }
        } catch (err) {
            console.error('Error in fetchDashboardData:', err);
            setError('Une erreur est survenue lors du chargement des données');
        } finally {
            loadingState(false);
        }
    }, [toast]);

    useEffect(() => {
        fetchDashboardData();
    }, [fetchDashboardData]);

    const handleRefresh = () => {
        fetchDashboardData(true);
    };

    const formatMonth = (dateString: string) => {
        try {
            const date = new Date(dateString);
            return format(date, 'MMM yyyy');
        } catch (e) {
            return dateString;
        }
    };

    if (isLoading) {
        return (
            <Flex justify="center" align="center" minH="50vh">
                <Spinner size="xl" />
            </Flex>
        );
    }

    if (error && !stats) {
        return (
            <Box textAlign="center" py={10} px={6}>
                <Icon as={FiAlertCircle} boxSize={12} color="red.500" mb={4} />
                <Heading as="h2" size="lg" mb={2}>
                    Erreur de chargement
                </Heading>
                <Text color="gray.600" mb={4}>
                    {error}
                </Text>
                <Button
                    colorScheme="blue"
                    onClick={handleRefresh}
                    leftIcon={<Icon as={FiRefreshCw} />}
                    isLoading={isRefreshing}
                >
                    Réessayer
                </Button>
            </Box>
        );
    }

    return (
        <Box p={{ base: 4, md: 6 }}>
            <Flex justify="space-between" align="center" mb={6}>
                <Heading as="h1" size="xl" color={textColor}>
                    Tableau de bord
                </Heading>
                <Button
                    leftIcon={<FiRefreshCw />}
                    onClick={handleRefresh}
                    isLoading={isRefreshing}
                    colorScheme="blue"
                    variant="outline"
                >
                    Actualiser
                </Button>
            </Flex>

            {/* Stats Grid */}
            {stats?.data?.totals && (
                <SimpleGrid columns={{ base: 1, md: 2, lg: 4 }} spacing={6} mb={8}>
                    <StatCard
                        title="Chiffre d'affaires"
                        value={stats.data.totals.revenue}
                        icon={FiDollarSign}
                        isCurrency
                        trend="up"
                        trendValue={12.5}
                    />
                    <StatCard
                        title="Factures totales"
                        value={stats.data.totals.invoices}
                        icon={FiFileText}
                        trend="up"
                        trendValue={8.3}
                    />
                    <StatCard
                        title="Entreprises"
                        value={stats.data.totals.companies}
                        icon={FiUsers}
                        trend="up"
                        trendValue={5.2}
                    />
                    <StatCard
                        title="Montant TVA"
                        value={stats.data.totals.tax}
                        icon={FiDollarSign}
                        isCurrency
                        trend="up"
                        trendValue={3.7}
                    />
                </SimpleGrid>
            )}

            {/* Status Summary */}
            {stats?.data?.status && (
                <Box
                    p={5}
                    bg={cardBg}
                    borderRadius="lg"
                    boxShadow="sm"
                    borderWidth="1px"
                    borderColor={borderColor}
                    mb={8}
                >
                    <Text fontSize="lg" fontWeight="medium" mb={4} color={textColor}>
                        État des factures
                    </Text>
                    <SimpleGrid columns={{ base: 2, md: 4 }} spacing={4}>
                        {Object.entries(stats.data.status).map(([status, count]) => (
                            <Box
                                key={status}
                                p={4}
                                bg={useColorModeValue('gray.50', 'gray.700')}
                                borderRadius="md"
                                borderLeftWidth="4px"
                                borderLeftColor={getStatusColor(status)}
                            >
                                <Text
                                    fontSize="sm"
                                    color="gray.500"
                                    textTransform="capitalize"
                                    mb={1}
                                >
                                    {getStatusLabel(status)}
                                </Text>
                                <Text
                                    fontSize="xl"
                                    fontWeight="bold"
                                    color={textColor}
                                >
                                    {count}
                                </Text>
                            </Box>
                        ))}
                    </SimpleGrid>
                </Box>
            )}

            {/* Charts */}
            <SimpleGrid columns={{ base: 1, lg: 2 }} spacing={6} mb={8}>
                {/* Revenue Chart */}
                <Box
                    p={5}
                    bg={cardBg}
                    borderRadius="lg"
                    boxShadow="sm"
                    borderWidth="1px"
                    borderColor={borderColor}
                >
                    <Text fontSize="lg" fontWeight="medium" mb={4} color={textColor}>
                        Revenus mensuels
                    </Text>
                    <Box height={300}>
                        <ResponsiveContainer width="100%" height="100%">
                            <LineChart
                                data={monthlyData}
                                margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
                            >
                                <CartesianGrid strokeDasharray="3 3" stroke={useColorModeValue('#eee', '#444')} />
                                <XAxis
                                    dataKey="month"
                                    tickFormatter={formatMonth}
                                    tick={{ fill: textColor }}
                                />
                                <YAxis
                                    tickFormatter={(value) =>
                                        new Intl.NumberFormat('fr-TN', {
                                            style: 'currency',
                                            currency: 'TND',
                                            maximumFractionDigits: 0,
                                            notation: 'compact'
                                        }).format(value).replace('TND', '')
                                    }
                                    tick={{ fill: textColor }}
                                    width={60}
                                />
                                <Tooltip
                                    content={<CustomTooltip />}
                                    formatter={(value: number) => [formatCurrency(value), '']}
                                />
                                <Legend />
                                <Line
                                    type="monotone"
                                    dataKey="total_amount"
                                    name="Revenu (TTC)"
                                    stroke="#4f46e5"
                                    strokeWidth={2}
                                    dot={{ r: 4 }}
                                    activeDot={{ r: 6 }}
                                />
                                <Line
                                    type="monotone"
                                    dataKey="tax_amount"
                                    name="TVA"
                                    stroke="#10b981"
                                    strokeWidth={2}
                                    dot={{ r: 4 }}
                                    activeDot={{ r: 6 }}
                                />
                            </LineChart>
                        </ResponsiveContainer>
                    </Box>
                </Box>

                {/* Invoices Chart */}
                <Box
                    p={5}
                    bg={cardBg}
                    borderRadius="lg"
                    boxShadow="sm"
                    borderWidth="1px"
                    borderColor={borderColor}
                >
                    <Text fontSize="lg" fontWeight="medium" mb={4} color={textColor}>
                        Nombre de factures
                    </Text>
                    <Box height={300}>
                        <ResponsiveContainer width="100%" height="100%">
                            <BarChart
                                data={monthlyData}
                                margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
                            >
                                <CartesianGrid strokeDasharray="3 3" stroke={useColorModeValue('#eee', '#444')} />
                                <XAxis
                                    dataKey="month"
                                    tickFormatter={formatMonth}
                                    tick={{ fill: textColor }}
                                />
                                <YAxis
                                    tick={{ fill: textColor }}
                                    width={30}
                                />
                                <Tooltip
                                    content={<CustomTooltip />}
                                    formatter={(value: number) => [value, 'Factures']}
                                />
                                <Legend />
                                <Bar
                                    dataKey="invoice_count"
                                    name="Nombre de factures"
                                    fill="#4f46e5"
                                    radius={[4, 4, 0, 0]}
                                />
                            </BarChart>
                        </ResponsiveContainer>
                    </Box>
                </Box>
            </SimpleGrid>
        </Box>
    );
};

// Helper function to get status color
const getStatusColor = (status: string): string => {
    const colors: Record<string, string> = {
        'draft': '#9ca3af',
        'sent': '#3b82f6',
        'paid': '#10b981',
        'overdue': '#ef4444',
        'cancelled': '#6b7280',
    };
    return colors[status.toLowerCase()] || '#6b7280';
};

// Helper function to get status label
const getStatusLabel = (status: string): string => {
    const labels: Record<string, string> = {
        'draft': 'Brouillon',
        'sent': 'Envoyées',
        'paid': 'Payées',
        'overdue': 'En retard',
        'cancelled': 'Annulées',
    };
    return labels[status.toLowerCase()] || status;
};

// StatCard component
const StatCard = ({
    title,
    value,
    icon,
    isCurrency = false,
    trend,
    trendValue
}: {
    title: string;
    value: number;
    icon: React.ElementType;
    isCurrency?: boolean;
    trend?: 'up' | 'down' | 'neutral';
    trendValue?: number;
}) => {
    const cardBg = useColorModeValue('white', 'gray.800');
    const textColor = useColorModeValue('gray.800', 'white');
    const trendColor = trend === 'up' ? 'green.500' : trend === 'down' ? 'red.500' : 'gray.500';

    return (
        <Box
            p={5}
            bg={cardBg}
            borderRadius="lg"
            boxShadow="sm"
            borderWidth="1px"
            borderColor="transparent"
            _hover={{
                borderColor: 'blue.200',
                transform: 'translateY(-2px)',
                transition: 'all 0.2s'
            }}
            transition="all 0.2s"
        >
            <HStack justify="space-between" align="flex-start">
                <Box>
                    <Text fontSize="sm" color="gray.500" mb={1}>
                        {title}
                    </Text>
                    <Text
                        fontSize="2xl"
                        fontWeight="bold"
                        color={textColor}
                        mb={2}
                    >
                        {isCurrency ? formatCurrency(value) : value}
                    </Text>
                    {trend && trendValue !== undefined && (
                        <HStack spacing={1} align="center">
                            <Stat>
                                <StatHelpText mb={0}>
                                    <StatArrow
                                        type={trend === 'up' ? 'increase' : 'decrease'}
                                        color={trendColor}
                                    />
                                    {trendValue}%
                                </StatHelpText>
                            </Stat>
                            <Text fontSize="sm" color="gray.500">
                                vs. période précédente
                            </Text>
                        </HStack>
                    )}
                </Box>
                <Box
                    p={3}
                    bg={useColorModeValue('blue.50', 'blue.900')}
                    borderRadius="full"
                    color={useColorModeValue('blue.500', 'blue.200')}
                >
                    <Icon as={icon} boxSize={5} />
                </Box>
            </HStack>
        </Box>
    );
};

export default Dashboard;