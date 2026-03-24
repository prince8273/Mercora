import React, { useState } from "react";
import { NavLink } from "react-router-dom";
import { Sidebar, SidebarBody, SidebarLink } from "@/components/ui/sidebar";
import { 
  LayoutDashboard, 
  Brain, 
  DollarSign, 
  Heart, 
  TrendingUp, 
  Settings,
  User
} from "lucide-react";
import { motion } from "framer-motion";
import { cn } from "@/lib/utils";
import { useAuth } from "@/contexts/AuthContext";
import { AnimatePresence } from "framer-motion";
import { X } from "lucide-react";

const navItems = [
  { path: '/dashboard/overview',    label: 'Dashboard', icon: LayoutDashboard },
  { path: '/dashboard/intelligence',label: 'Query',     icon: Brain },
  { path: '/dashboard/pricing',     label: 'Pricing',   icon: DollarSign },
  { path: '/dashboard/sentiment',   label: 'Sentiment', icon: Heart },
  { path: '/dashboard/forecast',    label: 'Forecast',  icon: TrendingUp },
  { path: '/dashboard/settings',    label: 'Settings',  icon: Settings },
];

export default function ModernSideNav({ 
  mobileOpen, 
  setMobileOpen 
}: { 
  mobileOpen?: boolean; 
  setMobileOpen?: (open: boolean) => void 
}) {
  const [open, setOpen] = useState(false);
  const { user } = useAuth();

  const allLinks = navItems.map(item => ({
    label: item.label,
    href: item.path,
    icon: <item.icon className="text-gray-600 h-5 w-5 flex-shrink-0" />,
  }));

  return (
    <>
      {/* Desktop sidebar */}
      <Sidebar open={open} setOpen={setOpen}>
        <SidebarBody className="justify-between gap-10">
          <div className="flex flex-col flex-1 overflow-y-auto overflow-x-hidden">
            {open ? <Logo /> : <LogoIcon />}
            <div className="mt-8 flex flex-col gap-2">
              {allLinks.map((link, idx) => (
                <SidebarLink key={idx} link={link} />
              ))}
            </div>
          </div>
          <div>
            <SidebarLink
              link={{
                label: user?.full_name || user?.email || "User",
                href: "/dashboard/settings",
                icon: (
                  <div className="h-7 w-7 flex-shrink-0 rounded-full bg-gradient-to-r from-blue-500 to-purple-600 flex items-center justify-center">
                    <User className="h-4 w-4 text-white" />
                  </div>
                ),
              }}
            />
          </div>
        </SidebarBody>
      </Sidebar>

      {/* Mobile drawer — icons only */}
      <AnimatePresence>
        {mobileOpen && (
          <>
            {/* Backdrop */}
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              transition={{ duration: 0.2 }}
              className="fixed inset-0 bg-black/40 z-[90] md:hidden"
              onClick={() => setMobileOpen?.(false)}
            />
            {/* Drawer */}
            <motion.div
              initial={{ x: "-100%", opacity: 0 }}
              animate={{ x: 0, opacity: 1 }}
              exit={{ x: "-100%", opacity: 0 }}
              transition={{ duration: 0.3, ease: "easeInOut" }}
              className="fixed top-0 left-0 h-full w-20 bg-white z-[100] flex flex-col items-center py-6 gap-6 shadow-xl md:hidden"
            >
              {/* Close */}
              <button
                className="absolute right-3 top-4 text-gray-500 hover:text-gray-800"
                onClick={() => setMobileOpen?.(false)}
              >
                <X size={18} />
              </button>

              {/* Logo */}
              <div className="h-8 w-8 bg-gradient-to-r from-blue-500 to-blue-600 rounded-lg flex-shrink-0 mt-2" />

              {/* Nav icons */}
              <nav className="flex flex-col items-center gap-5 flex-1 mt-4">
                {navItems.map((item) => (
                  <NavLink
                    key={item.path}
                    to={item.path}
                    onClick={() => setMobileOpen?.(false)}
                    className={({ isActive }) =>
                      cn(
                        "w-10 h-10 flex items-center justify-center rounded-xl transition-colors",
                        isActive
                          ? "bg-blue-50 text-blue-600"
                          : "text-gray-500 hover:bg-gray-100 hover:text-gray-800"
                      )
                    }
                    title={item.label}
                  >
                    <item.icon size={22} />
                  </NavLink>
                ))}
              </nav>

              {/* User avatar */}
              <NavLink
                to="/dashboard/settings"
                onClick={() => setMobileOpen?.(false)}
                className="w-9 h-9 rounded-full bg-gradient-to-r from-blue-500 to-purple-600 flex items-center justify-center"
              >
                <User className="h-4 w-4 text-white" />
              </NavLink>
            </motion.div>
          </>
        )}
      </AnimatePresence>
    </>
  );
}

export const Logo = () => {
  return (
    <div className="font-normal flex space-x-2 items-center text-sm text-gray-900 py-1 relative z-20">
      <div className="h-5 w-6 bg-gradient-to-r from-blue-500 to-blue-600 rounded-br-lg rounded-tr-sm rounded-tl-lg rounded-bl-sm flex-shrink-0" />
      <motion.span
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        className="font-medium text-gray-900 whitespace-pre"
      >
        E-commerce Intelligence
      </motion.span>
    </div>
  );
};

export const LogoIcon = () => {
  return (
    <div className="font-normal flex space-x-2 items-center text-sm text-gray-900 py-1 relative z-20">
      <div className="h-5 w-6 bg-gradient-to-r from-blue-500 to-blue-600 rounded-br-lg rounded-tr-sm rounded-tl-lg rounded-bl-sm flex-shrink-0" />
    </div>
  );
};