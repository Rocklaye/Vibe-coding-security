import { Link, useLocation } from "react-router";
import { useAuth } from "@/hooks/useAuth";
import { useState } from "react";
import {
  BookOpen,
  LayoutDashboard,
  Award,
  FileText,
  Menu,
  X,
  LogOut,
  User,
  Shield,
  GraduationCap,
} from "lucide-react";
import { Button } from "@/components/ui/button";

export function Layout({ children }: { children: React.ReactNode }) {
  const { user, isAuthenticated, logout } = useAuth();
  const location = useLocation();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const isAdmin = user?.role === "admin";

  const navItems = [
    { path: "/", label: "Accueil", icon: LayoutDashboard },
    { path: "/cours", label: "Cours", icon: BookOpen },
    { path: "/devoirs", label: "Devoirs", icon: FileText },
    { path: "/certificats", label: "Certificats", icon: Award },
    ...(isAdmin
      ? [{ path: "/admin", label: "Admin", icon: Shield }]
      : []),
  ];

  const isActive = (path: string) => {
    if (path === "/") return location.pathname === "/";
    return location.pathname.startsWith(path);
  };

  return (
    <div className="min-h-screen bg-[#FBF8F5]">
      {/* Header */}
      <header className="sticky top-0 z-50 bg-[#FBF8F5]/90 backdrop-blur-md border-b border-[#E0DCD7]">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            {/* Logo */}
            <Link to="/" className="flex items-center gap-2 group">
              <GraduationCap className="w-8 h-8 text-[#D4A853] transition-transform group-hover:scale-110" />
              <span className="font-serif text-2xl text-[#1A1A1A]">Aura</span>
            </Link>

            {/* Desktop Nav */}
            <nav className="hidden md:flex items-center gap-1">
              {navItems.map((item) => (
                <Link
                  key={item.path}
                  to={item.path}
                  className={`px-3 py-2 rounded-lg text-sm font-medium transition-all duration-200 ${
                    isActive(item.path)
                      ? "bg-[#F2EDE7] text-[#1A1A1A]"
                      : "text-[#6B6865] hover:text-[#1A1A1A] hover:bg-[#F2EDE7]/50"
                  }`}
                >
                  {item.label}
                </Link>
              ))}
            </nav>

            {/* User Actions */}
            <div className="flex items-center gap-3">
              {isAuthenticated && user ? (
                <div className="hidden sm:flex items-center gap-3">
                  <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-[#F2EDE7]">
                    <User className="w-4 h-4 text-[#6B6865]" />
                    <span className="text-sm font-medium text-[#1A1A1A]">
                      {user.name || "Utilisateur"}
                    </span>
                    {isAdmin && (
                      <Shield className="w-3.5 h-3.5 text-[#D4A853]" />
                    )}
                  </div>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={logout}
                    className="text-[#6B6865] hover:text-[#1A1A1A] hover:bg-[#F2EDE7]"
                  >
                    <LogOut className="w-4 h-4" />
                  </Button>
                </div>
              ) : (
                <Link
                  to="/login"
                  className="btn-gold text-sm py-2 px-4"
                >
                  Connexion
                </Link>
              )}

              {/* Mobile Menu Toggle */}
              <button
                className="md:hidden p-2 rounded-lg hover:bg-[#F2EDE7] transition-colors"
                onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              >
                {mobileMenuOpen ? (
                  <X className="w-5 h-5" />
                ) : (
                  <Menu className="w-5 h-5" />
                )}
              </button>
            </div>
          </div>
        </div>

        {/* Mobile Menu */}
        {mobileMenuOpen && (
          <div className="md:hidden border-t border-[#E0DCD7] bg-[#FBF8F5]">
            <nav className="px-4 py-3 space-y-1">
              {navItems.map((item) => {
                const Icon = item.icon;
                return (
                  <Link
                    key={item.path}
                    to={item.path}
                    onClick={() => setMobileMenuOpen(false)}
                    className={`flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all duration-200 ${
                      isActive(item.path)
                        ? "bg-[#F2EDE7] text-[#1A1A1A]"
                        : "text-[#6B6865] hover:text-[#1A1A1A] hover:bg-[#F2EDE7]/50"
                    }`}
                  >
                    <Icon className="w-4 h-4" />
                    {item.label}
                  </Link>
                );
              })}
              {isAuthenticated && (
                <button
                  onClick={() => {
                    logout();
                    setMobileMenuOpen(false);
                  }}
                  className="flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium text-[#6B6865] hover:text-[#1A1A1A] hover:bg-[#F2EDE7]/50 w-full"
                >
                  <LogOut className="w-4 h-4" />
                  Déconnexion
                </button>
              )}
            </nav>
          </div>
        )}
      </header>

      {/* Main Content */}
      <main>{children}</main>

      {/* Footer */}
      <footer className="border-t border-[#E0DCD7] bg-[#FBF8F5]">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
            <div>
              <div className="flex items-center gap-2 mb-4">
                <GraduationCap className="w-6 h-6 text-[#D4A853]" />
                <span className="font-serif text-xl">Aura</span>
              </div>
              <p className="text-sm text-[#6B6865]">
                Plateforme LMS haut de gamme dédiée à la formation continue.
              </p>
            </div>
            <div>
              <h4 className="font-dm font-semibold text-sm mb-3 text-[#1A1A1A]">
                Navigation
              </h4>
              <ul className="space-y-2">
                <li>
                  <Link to="/" className="text-sm text-[#6B6865] hover:text-[#D4A853] transition-colors">
                    Accueil
                  </Link>
                </li>
                <li>
                  <Link to="/cours" className="text-sm text-[#6B6865] hover:text-[#D4A853] transition-colors">
                    Cours
                  </Link>
                </li>
                <li>
                  <Link to="/forum" className="text-sm text-[#6B6865] hover:text-[#D4A853] transition-colors">
                    Forum
                  </Link>
                </li>
              </ul>
            </div>
            <div>
              <h4 className="font-dm font-semibold text-sm mb-3 text-[#1A1A1A]">
                Apprenant
              </h4>
              <ul className="space-y-2">
                <li>
                  <Link to="/devoirs" className="text-sm text-[#6B6865] hover:text-[#D4A853] transition-colors">
                    Mes devoirs
                  </Link>
                </li>
                <li>
                  <Link to="/certificats" className="text-sm text-[#6B6865] hover:text-[#D4A853] transition-colors">
                    Certificats
                  </Link>
                </li>
              </ul>
            </div>
            <div>
              <h4 className="font-dm font-semibold text-sm mb-3 text-[#1A1A1A]">
                Contact
              </h4>
              <p className="text-sm text-[#6B6865]">
                contact@aura-formation.fr
              </p>
              <p className="text-sm text-[#6B6865] mt-1">
                +33 1 23 45 67 89
              </p>
            </div>
          </div>
          <div className="mt-8 pt-8 border-t border-[#E0DCD7] text-center">
            <p className="text-xs text-[#6B6865]">
              © 2024 Aura Espace Formation. Tous droits réservés.
            </p>
          </div>
        </div>
      </footer>
    </div>
  );
}
