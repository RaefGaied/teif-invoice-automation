import React, { useState } from 'react';
import { Link as RouterLink, useNavigate, useLocation } from 'react-router-dom';
import {
    Box,
    Button,
    FormControl,
    FormLabel,
    Input,
    InputGroup,
    InputRightElement,
    VStack,
    Text,
    Link,
    useToast,
    FormErrorMessage,
    useColorModeValue,
    Icon,
    Divider,
    HStack,
} from '@chakra-ui/react';
import { ViewIcon, ViewOffIcon, LockIcon, EmailIcon, GoogleIcon, FacebookIcon } from '@chakra-ui/icons';
import { useForm } from 'react-hook-form';
import { yupResolver } from '@hookform/resolvers/yup';
import * as yup from 'yup';
import { useAuth } from '../contexts/AuthContext';

interface LoginFormData {
    email: string;
    password: string;
}

const schema = yup.object().shape({
    email: yup.string().email('Email invalide').required('Email est requis'),
    password: yup.string().required('Mot de passe est requis'),
});

const Login: React.FC = () => {
    const [showPassword, setShowPassword] = useState(false);
    const [isLoading, setIsLoading] = useState(false);
    const { login } = useAuth();
    const navigate = useNavigate();
    const location = useLocation();
    const toast = useToast();
    const from = (location.state as any)?.from?.pathname || '/dashboard';

    const {
        register,
        handleSubmit,
        formState: { errors },
    } = useForm<LoginFormData>({
        resolver: yupResolver(schema),
    });

    const onSubmit = async (data: LoginFormData) => {
        try {
            setIsLoading(true);
            await login(data.email, data.password);

            toast({
                title: 'Connexion réussie',
                description: 'Vous êtes maintenant connecté',
                status: 'success',
                duration: 3000,
                isClosable: true,
            });

            navigate(from, { replace: true });
        } catch (error) {
            console.error('Login error:', error);
            toast({
                title: 'Erreur de connexion',
                description: 'Email ou mot de passe incorrect',
                status: 'error',
                duration: 5000,
                isClosable: true,
            });
        } finally {
            setIsLoading(false);
        }
    };

    const handleSocialLogin = (provider: 'google' | 'facebook') => {
        // Implement social login logic here
        console.log(`Logging in with ${provider}`);
    };

    return (
        <Box>
            <Text fontSize="2xl" fontWeight="bold" mb={6} textAlign="center">
                Connectez-vous à votre compte
            </Text>

            <form onSubmit={handleSubmit(onSubmit)}>
                <VStack spacing={4}>
                    <FormControl id="email" isInvalid={!!errors.email}>
                        <FormLabel>Email</FormLabel>
                        <InputGroup>
                            <Input
                                type="email"
                                placeholder="votre@email.com"
                                {...register('email')}
                                autoComplete="email"
                            />
                        </InputGroup>
                        <FormErrorMessage>
                            {errors.email && errors.email.message}
                        </FormErrorMessage>
                    </FormControl>

                    <FormControl id="password" isInvalid={!!errors.password}>
                        <FormLabel>Mot de passe</FormLabel>
                        <InputGroup>
                            <Input
                                type={showPassword ? 'text' : 'password'}
                                placeholder="••••••••"
                                {...register('password')}
                                autoComplete="current-password"
                            />
                            <InputRightElement h="full">
                                <Button
                                    variant="ghost"
                                    onClick={() => setShowPassword(!showPassword)}
                                >
                                    {showPassword ? <ViewOffIcon /> : <ViewIcon />}
                                </Button>
                            </InputRightElement>
                        </InputGroup>
                        <FormErrorMessage>
                            {errors.password && errors.password.message}
                        </FormErrorMessage>
                    </FormControl>

                    <Link
                        as={RouterLink}
                        to="/forgot-password"
                        fontSize="sm"
                        color="blue.500"
                        alignSelf="flex-end"
                        _hover={{ textDecoration: 'underline' }}
                    >
                        Mot de passe oublié ?
                    </Link>

                    <Button
                        type="submit"
                        colorScheme="blue"
                        width="100%"
                        size="lg"
                        mt={4}
                        isLoading={isLoading}
                        loadingText="Connexion..."
                        leftIcon={<LockIcon />}
                    >
                        Se connecter
                    </Button>
                </VStack>
            </form>

            <Divider my={8} />

            <VStack spacing={4}>
                <Button
                    variant="outline"
                    width="100%"
                    leftIcon={<Icon as={GoogleIcon} />}
                    onClick={() => handleSocialLogin('google')}
                >
                    Continuer avec Google
                </Button>
                <Button
                    variant="outline"
                    width="100%"
                    leftIcon={<Icon as={FacebookIcon} color="#1877F2" />}
                    onClick={() => handleSocialLogin('facebook')}
                >
                    Continuer avec Facebook
                </Button>
            </VStack>

            <Text mt={6} textAlign="center" color={useColorModeValue('gray.600', 'gray.400')}>
                Pas encore de compte ?{' '}
                <Link
                    as={RouterLink}
                    to="/register"
                    color="blue.500"
                    _hover={{ textDecoration: 'underline' }}
                    fontWeight="medium"
                >
                    Créer un compte
                </Link>
            </Text>
        </Box>
    );
};

export default Login;
