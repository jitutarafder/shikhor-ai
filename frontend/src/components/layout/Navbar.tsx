import React, { useState } from 'react';
import { NavLink, Link } from 'react-router-dom';
import { Menu, X, Sprout, Globe, ShieldAlert, LayoutDashboard } from 'lucide-react';
import { useLocale } from '../../i18n/LocaleContext';
import { useAuth } from '../../features/auth/AuthContext';
import { NotificationBell } from '../../features/notifications/components/NotificationBell';
import { Button } from '../ui/Button';

export const Navbar: React.FC = () => {
  const { locale, setLocale, t } = useLocale();
  const { user } = useAuth();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const isAdminOrMod = user?.role?.toLowerCase() === 'admin' || user?.role?.toLowerCase() === 'moderator';

  const toggleLocale = () => {
    setLocale(locale === 'bn' ? 'en' : 'bn');
  };

  const navLinks = [
    { to: '/', label: t.nav.home },
    { to: '/features', label: t.nav.features },
    { to: '/about', label: t.nav.about },
    { to: '/contact', label: t.nav.contact },
  ];

  return (
    <header className="sticky top-0 z-40 w-full border-b border-line-200/80 bg-canvas/95 backdrop-blur supports-[backdrop-filter]:bg-canvas/80">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-[76px] flex items-center justify-between">
        {/* Brand Logo */}
        <Link to="/" className="flex items-center gap-2.5 focus-visible:ring-2 focus-visible:ring-forest-700 rounded-lg p-1">
          <div className="w-10 h-10 rounded-btn bg-leaf-100 border border-leaf-500/20 flex items-center justify-center text-forest-700">
            <Sprout className="w-6 h-6" />
          </div>
          <div>
            <span className="font-bold text-xl sm:text-2xl text-forest-900 tracking-tight block leading-tight">
              {t.brand.name}
            </span>
            <span className="text-[11px] text-ink-600 block sm:hidden">
              {locale === 'bn' ? 'ডিজিটাল কৃষি সহচর' : 'Agri AI'}
            </span>
          </div>
        </Link>

        {/* Desktop Navigation */}
        <nav className="hidden md:flex items-center gap-8" aria-label="Main Navigation">
          {navLinks.map((link) => (
            <NavLink
              key={link.to}
              to={link.to}
              className={({ isActive }) =>
                `text-base font-medium py-2 transition-colors relative ${
                  isActive
                    ? 'text-forest-900 font-semibold after:absolute after:bottom-0 after:left-0 after:right-0 after:h-[2px] after:bg-forest-700'
                    : 'text-ink-600 hover:text-forest-700'
                }`
              }
            >
              {link.label}
            </NavLink>
          ))}
        </nav>

        {/* Right Actions: Language & Auth */}
        <div className="hidden md:flex items-center gap-3">
          <button
            onClick={toggleLocale}
            className="flex items-center gap-1.5 px-3 py-2 text-sm font-medium text-ink-600 hover:text-forest-700 rounded-btn border border-line-200 hover:border-forest-700 transition-colors"
            title="Switch Language / ভাষা পরিবর্তন"
            aria-label="Switch Language"
          >
            <Globe className="w-4 h-4 text-leaf-500" />
            <span>{locale === 'bn' ? 'EN' : 'বাংলা'}</span>
          </button>

          {user && <NotificationBell />}

          {user ? (
            <div className="flex items-center gap-2.5">
              {isAdminOrMod && (
                <Link to="/app/admin">
                  <Button variant="danger" size="sm" className="bg-rose-700 hover:bg-rose-800 text-white text-xs px-3 py-1.5 flex items-center gap-1.5 shadow-xs font-bold border-none">
                    <ShieldAlert className="w-3.5 h-3.5 text-white" />
                    <span>অ্যাডমিন প্যানেল</span>
                  </Button>
                </Link>
              )}
              <Link to="/app">
                <Button variant="outline" size="sm" className="text-xs flex items-center gap-1.5">
                  <LayoutDashboard className="w-3.5 h-3.5 text-forest-700" />
                  <span>ড্যাশবোর্ড</span>
                  {!isAdminOrMod && user.nidVerificationStatus !== 'approved' && (
                    <span className="text-[10px] font-bold text-amber-800 bg-amber-100 border border-amber-300 px-1.5 py-0.5 rounded-full">
                      ⏳ অপেক্ষমাণ
                    </span>
                  )}
                </Button>
              </Link>
            </div>
          ) : (
            <div className="flex items-center gap-2">
              <Link to="/login">
                <Button variant="ghost" size="sm">
                  {t.nav.login}
                </Button>
              </Link>
              <Link to="/signup">
                <Button variant="primary" size="sm">
                  {t.nav.signup}
                </Button>
              </Link>
            </div>
          )}
        </div>

        {/* Mobile Menu Button */}
        <div className="flex md:hidden items-center gap-2">
          {user && <NotificationBell />}

          <button
            onClick={toggleLocale}
            className="px-2.5 py-1.5 text-xs font-semibold text-forest-700 bg-leaf-100 rounded-btn border border-leaf-500/20"
            aria-label="Toggle language"
          >
            {locale === 'bn' ? 'EN' : 'বাং'}
          </button>

          <button
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            className="w-11 h-11 flex items-center justify-center rounded-btn text-ink-900 hover:bg-surface border border-line-200"
            aria-label="Open navigation menu"
            aria-expanded={mobileMenuOpen}
          >
            {mobileMenuOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
          </button>
        </div>
      </div>

      {/* Mobile Drawer */}
      {mobileMenuOpen && (
        <div className="md:hidden border-b border-line-200 bg-canvas px-4 pt-3 pb-6 space-y-4 shadow-lg animate-in slide-in-from-top duration-200">
          <nav className="flex flex-col space-y-1">
            {navLinks.map((link) => (
              <NavLink
                key={link.to}
                to={link.to}
                onClick={() => setMobileMenuOpen(false)}
                className={({ isActive }) =>
                  `px-3 py-3 rounded-btn text-base font-medium flex items-center justify-between ${
                    isActive ? 'bg-leaf-100 text-forest-900 font-semibold' : 'text-ink-600 hover:bg-surface'
                  }`
                }
              >
                {link.label}
              </NavLink>
            ))}
          </nav>
          <div className="pt-2 border-t border-line-200 flex flex-col gap-2.5">
            {user ? (
              <>
                {isAdminOrMod && (
                  <Link to="/app/admin" onClick={() => setMobileMenuOpen(false)}>
                    <Button variant="danger" fullWidth size="md" className="bg-rose-700 hover:bg-rose-800 text-white flex items-center justify-center gap-2 font-bold">
                      <ShieldAlert className="w-4 h-4 text-white" />
                      <span>অ্যাডমিন ও মডারেশন প্যানেল</span>
                    </Button>
                  </Link>
                )}
                <Link to="/app" onClick={() => setMobileMenuOpen(false)}>
                  <Button variant="outline" fullWidth size="md" className="flex items-center justify-center gap-2">
                    <LayoutDashboard className="w-4 h-4 text-forest-700" />
                    <span>মূল ড্যাশবোর্ড ({user.fullName})</span>
                  </Button>
                </Link>
              </>
            ) : (
              <>
                <Link to="/login" onClick={() => setMobileMenuOpen(false)}>
                  <Button variant="outline" fullWidth size="md">
                    {t.nav.login}
                  </Button>
                </Link>
                <Link to="/signup" onClick={() => setMobileMenuOpen(false)}>
                  <Button variant="primary" fullWidth size="md">
                    {t.nav.signup}
                  </Button>
                </Link>
              </>
            )}
          </div>
        </div>
      )}
    </header>
  );
};
