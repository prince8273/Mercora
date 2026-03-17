import React, { useState } from "react";
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

const navItems = [
  {
    section: 'Overview',
    items: [
      { 
        path: '/dashboard/overview', 
        label: 'Dashboard', 
        icon: <LayoutDashboard className="text-gray-600 h-5 w-5 flex-shrink-0" />
      },
    ],
  },
  {
    section: 'Intelligence',
    items: [
      { 
        path: '/dashboard/intelligence', 
        label: 'Query', 
        icon: <Brain className="text-gray-600 h-5 w-5 flex-shrink-0" />
      },
    ],
  },
  {
    section: 'Analytics',
    items: [
      { 
        path: '/dashboard/pricing', 
        label: 'Pricing', 
        icon: <DollarSign className="text-gray-600 h-5 w-5 flex-shrink-0" />
      },
      { 
        path: '/dashboard/sentiment', 
        label: 'Sentiment', 
        icon: <Heart className="text-gray-600 h-5 w-5 flex-shrink-0" />
      },
      { 
        path: '/dashboard/forecast', 
        label: 'Forecast', 
        icon: <TrendingUp className="text-gray-600 h-5 w-5 flex-shrink-0" />
      },
    ],
  },
  {
    section: 'Settings',
    items: [
      { 
        path: '/dashboard/settings', 
        label: 'Settings', 
        icon: <Settings className="text-gray-600 h-5 w-5 flex-shrink-0" />
      },
    ],
  },
];

export default function ModernSideNav() {
  const [open, setOpen] = useState(false);
  const { user } = useAuth();

  // Flatten all navigation items for the sidebar
  const allLinks = navItems.flatMap(section => section.items.map(item => ({
    label: item.label,
    href: item.path,
    icon: item.icon,
  })));

  return (
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