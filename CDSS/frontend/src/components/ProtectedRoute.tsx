/**
 * ProtectedRoute.tsx
 * Wraps any route that requires the user to be logged in.
 * If no JWT token is found → redirect to /login.
 */
import { Navigate, Outlet } from 'react-router-dom';
import { isLoggedIn } from '../utils/auth';

export default function ProtectedRoute() {
  if (!isLoggedIn()) {
    return <Navigate to="/login" replace />;
  }
  return <Outlet />;
}
