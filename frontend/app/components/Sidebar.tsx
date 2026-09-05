"use client";

import Link from "next/link";
import Image from "next/image";
import { usePathname } from "next/navigation";
import { Home, FileText, BarChart2, Settings, ChevronLeft, ChevronRight, Activity } from "lucide-react";

interface SidebarProps {
  collapsed: boolean;
  onToggle: () => void;
  mobileMenuOpen?: boolean;
  onMobileClose?: () => void;
}

export function Sidebar({ collapsed, onToggle, mobileMenuOpen, onMobileClose }: SidebarProps) {
  const pathname = usePathname();

  const navItems = [
    { name: "Overview", href: "/", icon: Home },
    { name: "Recovery Cases", href: "/cases", icon: FileText },
    { name: "Analytics", href: "/analytics", icon: BarChart2 },
    { name: "Evaluation", href: "/evaluation", icon: Activity },
  ];

  return (
    <>
      {/* Mobile Overlay */}
      {mobileMenuOpen && (
        <div
          className="md:hidden fixed inset-0 bg-fintech-navy/50 z-40 backdrop-blur-sm transition-opacity"
          onClick={onMobileClose}
        />
      )}

      <aside
        className={`
          ${collapsed ? "md:w-[72px]" : "md:w-[220px]"}
          ${mobileMenuOpen ? "translate-x-0" : "-translate-x-full md:translate-x-0"}
          fixed md:sticky top-0 left-0 h-screen shrink-0 z-50 transition-all duration-300 border-r border-[#082d5c] select-none
          bg-[#0B3B78] flex flex-col items-center py-5
          w-[240px] md:w-auto
        `}
      >
        {/* Subtle Collapse/Expand Toggle Button - Hidden on Mobile */}
        <button
          onClick={onToggle}
          aria-label={collapsed ? "Expand sidebar" : "Collapse sidebar"}
          className="hidden md:flex absolute -right-3 top-6 w-6 h-6 rounded-full bg-[#0B3B78] border border-white/20 text-white/90 items-center justify-center hover:bg-[#146BFF] hover:border-[#146BFF] hover:text-white transition-all shadow-md z-40 focus:outline-none"
        >
          {collapsed ? (
            <ChevronRight className="w-3.5 h-3.5" />
          ) : (
            <ChevronLeft className="w-3.5 h-3.5" />
          )}
        </button>

        {/* Brand Header */}
        <div className={`mb-7 flex items-center w-full ${collapsed ? "md:justify-center px-4 md:px-0" : "justify-start px-4"}`}>
          {collapsed ? (
            <>
              <div className="hidden md:flex w-10 h-10 items-center justify-center shrink-0">
                <Image
                  src="/revive-icon.png"
                  alt="REVIVE Logo"
                  width={34}
                  height={34}
                  className="object-contain"
                  priority
                />
              </div>
              <div className="md:hidden h-10 flex items-center shrink-0">
                <Image
                  src="/revive-logo-horizontal-white.png"
                  alt="REVIVE - Recover. Retain. Grow."
                  width={175}
                  height={30}
                  className="object-contain"
                  priority
                />
              </div>
            </>
          ) : (
            <div className="h-10 flex items-center shrink-0">
              <Image
                src="/revive-logo-horizontal-white.png"
                alt="REVIVE - Recover. Retain. Grow."
                width={175}
                height={30}
                className="object-contain"
                priority
              />
            </div>
          )}
        </div>

        {/* Navigation Items */}
        <nav className={`flex-1 w-full flex flex-col gap-1.5 ${collapsed ? "px-3 md:px-2.5 md:items-center" : "px-3"}`}>
          {navItems.map((item) => {
            const isActive = pathname === item.href || (item.href !== "/" && pathname?.startsWith(item.href));

            return (
              <div key={item.name} className="relative group w-full flex justify-center">
                <Link
                  href={item.href}
                  onClick={() => onMobileClose?.()}
                  className={`flex items-center rounded-lg transition-all duration-200 w-full relative ${
                    collapsed ? "md:w-11 md:h-11 md:justify-center md:p-0 px-3 py-2.5 gap-3" : "px-3 py-2.5 gap-3"
                  } ${
                    isActive
                      ? "bg-white/15 text-white font-medium shadow-xs"
                      : "text-blue-100/70 hover:bg-white/10 hover:text-white"
                  }`}
                >
                  {/* Active route visual indicator */}
                  {isActive && (
                    <span className="absolute left-0 top-1/2 -translate-y-1/2 w-1 h-5 bg-[#146BFF] rounded-r-full" />
                  )}

                  <item.icon className={`w-5 h-5 shrink-0 ${isActive ? "text-white" : "text-blue-200/80"}`} />

                  {(!collapsed || mobileMenuOpen) && (
                    <span className={`text-xs font-medium whitespace-nowrap overflow-hidden text-ellipsis ${collapsed ? "md:hidden" : ""}`}>
                      {item.name}
                    </span>
                  )}
                </Link>

                {/* Tooltip on Hover (When Collapsed - Desktop Only) */}
                {collapsed && !mobileMenuOpen && (
                  <div className="hidden md:block absolute left-[calc(100%+12px)] top-1/2 -translate-y-1/2 pointer-events-none opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all duration-150 z-50">
                    <div className="bg-[#0F1F3D] text-white text-xs font-medium px-2.5 py-1.5 rounded-md shadow-lg whitespace-nowrap border border-slate-700">
                      {item.name}
                    </div>
                  </div>
                )}
              </div>
            );
          })}
        </nav>

        {/* Footer Section: Settings & User Profile */}
        <div className={`w-full flex flex-col gap-2 mt-auto ${collapsed ? "px-3 md:px-2.5 md:items-center" : "px-3"}`}>
          {/* Settings */}
          <div className="relative group w-full flex justify-center">
            <button
              className={`flex items-center rounded-lg transition-all duration-200 text-blue-100/70 hover:bg-white/10 hover:text-white w-full ${
                collapsed ? "md:w-11 md:h-11 md:justify-center md:p-0 px-3 py-2.5 gap-3" : "px-3 py-2.5 gap-3"
              }`}
            >
              <Settings className="w-5 h-5 shrink-0 text-blue-200/80" />
              {(!collapsed || mobileMenuOpen) && (
                <span className={`text-xs font-medium whitespace-nowrap ${collapsed ? "md:hidden" : ""}`}>Settings</span>
              )}
            </button>

            {collapsed && !mobileMenuOpen && (
              <div className="hidden md:block absolute left-[calc(100%+12px)] top-1/2 -translate-y-1/2 pointer-events-none opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all duration-150 z-50">
                <div className="bg-[#0F1F3D] text-white text-xs font-medium px-2.5 py-1.5 rounded-md shadow-lg whitespace-nowrap border border-slate-700">
                  Settings
                </div>
              </div>
            )}
          </div>

          {/* User Profile Avatar */}
          <div className="relative group w-full flex justify-center">
            <div
              className={`flex items-center w-full transition-all duration-200 rounded-lg ${
                collapsed
                  ? "md:w-11 md:h-11 md:justify-center md:p-0 gap-2.5 px-3 py-2 bg-white/5 md:bg-transparent md:border-none border border-white/10"
                  : "gap-2.5 px-3 py-2 bg-white/5 border border-white/10"
              }`}
            >
              <div className="w-8 h-8 rounded-full bg-[#146BFF] flex items-center justify-center text-white text-xs font-bold shrink-0 shadow-sm">
                A
              </div>
              {(!collapsed || mobileMenuOpen) && (
                <div className={`flex flex-col overflow-hidden text-left ${collapsed ? "md:hidden" : ""}`}>
                  <span className="text-white text-xs font-semibold truncate leading-tight">Acme Payments</span>
                  <span className="text-blue-200/60 text-[10px] truncate leading-tight">merchant_demo</span>
                </div>
              )}
            </div>

            {collapsed && !mobileMenuOpen && (
              <div className="hidden md:block absolute left-[calc(100%+12px)] top-1/2 -translate-y-1/2 pointer-events-none opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all duration-150 z-50">
                <div className="bg-[#0F1F3D] text-white text-xs font-medium px-2.5 py-1.5 rounded-md shadow-lg whitespace-nowrap border border-slate-700">
                  Acme Payments
                </div>
              </div>
            )}
          </div>
        </div>
      </aside>
    </>
  );
}
