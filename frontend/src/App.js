import { useState, useEffect, createContext, useContext } from "react";
import "@/App.css";
import { BrowserRouter, Routes, Route, Navigate, useNavigate } from "react-router-dom";
import axios from "axios";
import { Toaster } from "@/components/ui/sonner";
import { toast } from "sonner";

// Pages
import LoginPage from "@/pages/LoginPage";
import AdminDashboard from "@/pages/AdminDashboard";
import OpportunityDetail from "@/pages/OpportunityDetail";
import ExporterDashboard from "@/pages/ExporterDashboard";
import PipelineView from "@/pages/PipelineView";
import CreateOpportunity from "@/pages/CreateOpportunity";
import ExporterProfile from "@/pages/ExporterProfile";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
export const API = `${BACKEND_URL}/api`;

// Auth Context
const AuthContext = createContext(null);

export const useAuth = () => useContext(AuthContext);

const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(localStorage.getItem("token"));
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const verifyToken = async () => {
      if (token) {
        try {
          const res = await axios.get(`${API}/auth/me`, {
            headers: { Authorization: `Bearer ${token}` }
          });
          setUser(res.data);
        } catch (e) {
          localStorage.removeItem("token");
          setToken(null);
          setUser(null);
        }
      }
      setLoading(false);
    };
    verifyToken();
  }, [token]);

  const login = async (email, password) => {
    const res = await axios.post(`${API}/auth/login`, { email, password });
    localStorage.setItem("token", res.data.access_token);
    setToken(res.data.access_token);
    setUser(res.data.user);
    return res.data.user;
  };

  const register = async (email, password, companyName, role) => {
    const res = await axios.post(`${API}/auth/register`, {
      email,
      password,
      company_name: companyName,
      role
    });
    localStorage.setItem("token", res.data.access_token);
    setToken(res.data.access_token);
    setUser(res.data.user);
    return res.data.user;
  };

  const logout = () => {
    localStorage.removeItem("token");
    setToken(null);
    setUser(null);
  };

  const authAxios = axios.create({
    baseURL: API,
    headers: token ? { Authorization: `Bearer ${token}` } : {}
  });

  return (
    <AuthContext.Provider value={{ user, token, login, register, logout, loading, authAxios }}>
      {children}
    </AuthContext.Provider>
  );
};

// Protected Route
const ProtectedRoute = ({ children, allowedRoles }) => {
  const { user, loading } = useAuth();

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-offwhite">
        <div className="text-slate-500">Loading...</div>
      </div>
    );
  }

  if (!user) {
    return <Navigate to="/login" replace />;
  }

  if (allowedRoles && !allowedRoles.includes(user.role)) {
    return <Navigate to={user.role === "admin" ? "/admin" : "/exporter"} replace />;
  }

  return children;
};

function AppRoutes() {
  const { user, loading } = useAuth();

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-offwhite">
        <div className="text-slate-500">Loading...</div>
      </div>
    );
  }

  return (
    <Routes>
      <Route path="/login" element={user ? <Navigate to={user.role === "admin" ? "/admin" : "/exporter"} /> : <LoginPage />} />
      
      {/* Admin Routes */}
      <Route path="/admin" element={<ProtectedRoute allowedRoles={["admin"]}><AdminDashboard /></ProtectedRoute>} />
      <Route path="/admin/opportunity/:id" element={<ProtectedRoute allowedRoles={["admin"]}><OpportunityDetail /></ProtectedRoute>} />
      <Route path="/admin/create-opportunity" element={<ProtectedRoute allowedRoles={["admin"]}><CreateOpportunity /></ProtectedRoute>} />
      <Route path="/admin/pipeline" element={<ProtectedRoute allowedRoles={["admin"]}><PipelineView /></ProtectedRoute>} />
      
      {/* Exporter Routes */}
      <Route path="/exporter" element={<ProtectedRoute allowedRoles={["exporter"]}><ExporterDashboard /></ProtectedRoute>} />
      <Route path="/exporter/profile" element={<ProtectedRoute allowedRoles={["exporter"]}><ExporterProfile /></ProtectedRoute>} />
      <Route path="/exporter/opportunity/:id" element={<ProtectedRoute allowedRoles={["exporter"]}><OpportunityDetail /></ProtectedRoute>} />
      
      {/* Default redirect */}
      <Route path="/" element={<Navigate to="/login" replace />} />
      <Route path="*" element={<Navigate to="/login" replace />} />
    </Routes>
  );
}

function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Toaster position="top-right" richColors />
        <AppRoutes />
      </AuthProvider>
    </BrowserRouter>
  );
}

export default App;
