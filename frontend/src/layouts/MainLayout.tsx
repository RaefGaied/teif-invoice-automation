import React from 'react';
import { Outlet } from 'react-router-dom';
import {
    Box,
    Flex,
    useColorModeValue,
    useDisclosure,
    useColorMode,
    IconButton,
    Avatar,
    Menu,
    MenuButton,
    MenuList,
    MenuItem,
    MenuDivider,
    Text,
    VStack,
    HStack,
    useToast,
    Button,
} from '@chakra-ui/react';
import { FiMenu, FiMoon, FiSun, FiBell, FiLogOut, FiUser, FiSettings } from 'react-icons/fi';
import Sidebar from '../components/navigation/Sidebar';
import { useAuth } from '../contexts/AuthContext';

const MainLayout: React.FC = () => {
    const { colorMode, toggleColorMode } = useColorMode();
    const { isOpen, onOpen, onClose } = useDisclosure();
    const { user, logout } = useAuth();
    const toast = useToast();
    const bgColor = useColorModeValue('white', 'gray.800');
    const borderColor = useColorModeValue('gray.200', 'gray.700');

    const handleLogout = async () => {
        try {
            await logout();
            toast({
                title: 'Déconnexion réussie',
                status: 'success',
                duration: 3000,
                isClosable: true,
            });
        } catch (error) {
            console.error('Logout error:', error);
            toast({
                title: 'Erreur de déconnexion',
                description: 'Une erreur est survenue lors de la déconnexion',
                status: 'error',
                duration: 5000,
                isClosable: true,
            });
        }
    };

    return (
        <Box minH="100vh" bg={useColorModeValue('gray.50', 'gray.900')}>
            {/* Sidebar */}
            <Sidebar isOpen={isOpen} onClose={onClose} />

            {/* Content */}
            <Box ml={{ base: 0, md: 60 }} transition="0.2s">
                {/* Header */}
                <Flex
                    as="header"
                    align="center"
                    justify="space-between"
                    w="full"
                    px="4"
                    bg={bgColor}
                    borderBottomWidth="1px"
                    borderColor={borderColor}
                    h="16"
                    position="sticky"
                    top={0}
                    zIndex="sticky"
                >
                    <HStack spacing={4}>
                        <IconButton
                            aria-label="Open menu"
                            display={{ base: 'flex', md: 'none' }}
                            onClick={onOpen}
                            icon={<FiMenu />}
                            variant="ghost"
                        />
                        <Text fontWeight="bold" fontSize="xl">
                            TEIF Invoice
                        </Text>
                    </HStack>

                    <HStack spacing={{ base: 2, md: 4 }}>
                        <IconButton
                            aria-label="Toggle color mode"
                            icon={colorMode === 'light' ? <FiMoon /> : <FiSun />}
                            onClick={toggleColorMode}
                            variant="ghost"
                        />

                        <IconButton
                            aria-label="Notifications"
                            icon={<FiBell />}
                            variant="ghost"
                            position="relative"
                        >
                            <Box
                                position="absolute"
                                top="2"
                                right="2"
                                w="2"
                                h="2"
                                bg="red.500"
                                borderRadius="full"
                            />
                        </IconButton>

                        <Menu>
                            <MenuButton
                                as={Button}
                                variant="ghost"
                                rounded="full"
                                minW={0}
                                px={2}
                            >
                                <HStack spacing={3}>
                                    <VStack
                                        display={{ base: 'none', md: 'flex' }}
                                        alignItems="flex-start"
                                        spacing={0}
                                        mr={2}
                                    >
                                        <Text fontSize="sm" fontWeight="medium">
                                            {user?.name || 'Utilisateur'}
                                        </Text>
                                        <Text fontSize="xs" color="gray.500">
                                            {user?.role || 'Rôle'}
                                        </Text>
                                    </VStack>
                                    <Avatar
                                        size="sm"
                                        name={user?.name || 'User'}
                                        bg={useColorModeValue('blue.500', 'blue.200')}
                                        color={useColorModeValue('white', 'gray.800')}
                                    />
                                </HStack>
                            </MenuButton>
                            <MenuList zIndex="dropdown">
                                <MenuItem icon={<FiUser />}>
                                    Mon profil
                                </MenuItem>
                                <MenuItem icon={<FiSettings />}>
                                    Paramètres
                                </MenuItem>
                                <MenuDivider />
                                <MenuItem
                                    icon={<FiLogOut />}
                                    onClick={handleLogout}
                                    color="red.500"
                                >
                                    Déconnexion
                                </MenuItem>
                            </MenuList>
                        </Menu>
                    </HStack>
                </Flex>

                {/* Main Content */}
                <Box as="main" p={4}>
                    <Outlet />
                </Box>
            </Box>
        </Box>
    );
};

export default MainLayout;
