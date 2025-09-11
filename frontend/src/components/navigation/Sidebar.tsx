import React from 'react';
import {
    Box,
    Drawer,
    DrawerContent,
    useDisclosure,
    VStack,
    Icon,
    Text,
    Link as ChakraLink,
    Flex,
    IconButton,
    Divider,
    useColorModeValue,
} from '@chakra-ui/react';
import { Link as RouterLink, useLocation } from 'react-router-dom';
import {
    FiHome,
    FiFileText,
    FiUpload,
    FiDollarSign,
    FiUsers,
    FiSettings,
    FiX,
} from 'react-icons/fi';

interface NavItemProps {
    icon: any;
    to: string;
    children: React.ReactNode;
    onClose: () => void;
}

const NavItem: React.FC<NavItemProps> = ({ icon, to, children, onClose }) => {
    const location = useLocation();
    const isActive = location.pathname === to;
    const activeBg = useColorModeValue('blue.50', 'blue.900');
    const activeColor = useColorModeValue('blue.600', 'blue.200');
    const hoverBg = useColorModeValue('gray.100', 'gray.700');

    return (
        <ChakraLink
            as={RouterLink}
            to={to}
            w="full"
            px={4}
            py={3}
            display="flex"
            alignItems="center"
            rounded="md"
            bg={isActive ? activeBg : 'transparent'}
            color={isActive ? activeColor : 'inherit'}
            _hover={{
                textDecoration: 'none',
                bg: isActive ? activeBg : hoverBg,
            }}
            onClick={onClose}
        >
            <Icon as={icon} mr={3} boxSize={5} />
            <Text fontSize="md">{children}</Text>
        </ChakraLink>
    );
};

interface SidebarProps {
    isOpen: boolean;
    onClose: () => void;
}

const Sidebar: React.FC<SidebarProps> = ({ isOpen, onClose }) => {
    const bgColor = useColorModeValue('white', 'gray.800');
    const borderColor = useColorModeValue('gray.200', 'gray.700');

    const navItems = [
        { icon: FiHome, to: '/dashboard', label: 'Tableau de bord' },
        { icon: FiFileText, to: '/invoices', label: 'Factures' },
        { icon: FiUpload, to: '/invoices/upload', label: 'Nouvelle facture' },
        { icon: FiDollarSign, to: '/payments', label: 'Paiements' },
        { icon: FiUsers, to: '/clients', label: 'Clients' },
    ];

    const sidebarContent = (
        <VStack h="full" w="60" position="fixed" bg={bgColor} borderRightWidth="1px" borderColor={borderColor}>
            {/* Sidebar Header */}
            <Flex w="full" h="16" align="center" justify="space-between" px={4} borderBottomWidth="1px" borderColor={borderColor}>
                <Text fontSize="xl" fontWeight="bold">TEIF Invoice</Text>
                <IconButton
                    aria-label="Close menu"
                    icon={<FiX />}
                    onClick={onClose}
                    display={{ base: 'flex', md: 'none' }}
                    variant="ghost"
                />
            </Flex>

            {/* Navigation Items */}
            <VStack w="full" p={4} spacing={2} align="stretch" overflowY="auto" flex={1}>
                {navItems.map((item) => (
                    <NavItem key={item.to} icon={item.icon} to={item.to} onClose={onClose}>
                        {item.label}
                    </NavItem>
                ))}
            </VStack>

            {/* Bottom Section */}
            <Box w="full" p={4} borderTopWidth="1px" borderColor={borderColor}>
                <NavItem icon={FiSettings} to="/settings" onClose={onClose}>
                    Paramètres
                </NavItem>
            </Box>
        </VStack>
    );

    return (
        <>
            {/* Mobile */}
            <Drawer
                isOpen={isOpen}
                placement="left"
                onClose={onClose}
                returnFocusOnClose={false}
                onOverlayClick={onClose}
                size="xs"
            >
                <DrawerContent maxW="60">
                    {sidebarContent}
                </DrawerContent>
            </Drawer>

            {/* Desktop */}
            <Box display={{ base: 'none', md: 'block' }}>
                {sidebarContent}
            </Box>
        </>
    );
};

export default Sidebar;
