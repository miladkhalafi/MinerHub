import { Routes, Route, Link, useNavigate } from "react-router-dom";
import { AuthProvider, useAuth } from "./context/AuthContext";
import ProtectedRoute from "./components/ProtectedRoute";
import { Button } from "./components/ui/button";
import Farms from "./pages/Farms";
import FarmDetail from "./pages/FarmDetail";
import Login from "./pages/Login";
import Users from "./pages/Users";
import { Users as UsersIcon, LogOut } from "lucide-react";

const API = "/api";

export { API };

function Nav() {
  const { user, logout, isAdmin } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate("/login");
  };

  return (
    <nav className="flex items-center justify-between border-b border-slate-700/50 bg-slate-900/50 px-6 py-4">
      <div className="flex items-center gap-8">
        <Link
          to="/"
          className="flex items-center gap-2 text-lg font-semibold text-slate-100 hover:text-sky-400 transition-colors"
        >
          <img src="/logo.png" alt="MinerHub" className="h-8" />
          Miner Agent
        </Link>
        {user && (
          <div className="flex items-center gap-4">
            <Link
              to="/"
              className="text-sm text-slate-400 hover:text-slate-200 transition-colors"
            >
              Farms
            </Link>
            {isAdmin && (
              <Link
                to="/users"
                className="flex items-center gap-1.5 text-sm text-slate-400 hover:text-slate-200 transition-colors"
              >
                <UsersIcon className="h-4 w-4" />
                Users
              </Link>
            )}
          </div>
        )}
      </div>
      {user && (
        <div className="flex items-center gap-4">
          <span className="text-sm text-slate-500">{user.email}</span>
          <Button variant="ghost" size="sm" onClick={handleLogout} className="gap-1.5">
            <LogOut className="h-4 w-4" />
            Logout
          </Button>
        </div>
      )}
    </nav>
  );
}

function AppLayout() {
  return (
    <div className="min-h-screen bg-slate-950">
      <Nav />
      <main className="mx-auto max-w-6xl px-6 py-8">
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route
            path="/"
            element={
              <ProtectedRoute>
                <Farms />
              </ProtectedRoute>
            }
          />
          <Route
            path="/farms/:id"
            element={
              <ProtectedRoute>
                <FarmDetail />
              </ProtectedRoute>
            }
          />
          <Route
            path="/users"
            element={
              <ProtectedRoute requireAdmin>
                <Users />
              </ProtectedRoute>
            }
          />
        </Routes>
      </main>
    </div>
  );
}

export default function App() {
  return (
    <AuthProvider>
      <AppLayout />
    </AuthProvider>
  );
}
