import React from 'react';
import { Navigate, Outlet, useLocation } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import { Box, Spinner, Center } from '@chakra-ui/react';

interface ProtectedRouteProps {
    roles?: string[];
    redirectPath?: string;
}

const ProtectedRoute: React.FC<ProtectedRouteProps> = ({
    roles = [],
    redirectPath = '/login',
}) => {
    const { isAuthenticated, user, loading } = useAuth();
    const location = useLocation();

    if (loading) {
        return (
            <Center minH="100vh">
                <Spinner size="xl" />
            </Center>
        );
    }

    if (!isAuthenticated) {
        return <Navigate to={redirectPath} state={{ from: location }} replace />;
    }

    if (roles.length > 0 && user && !roles.includes(user.role)) {
        return <Navigate to="/unauthorized" state={{ from: location }} replace />;
    }

    return <Outlet />;
};

export default ProtectedRoute;
