"use client";

import { Search, Calendar, ChevronDown, Menu } from "lucide-react";

interface TopbarProps {
  onMobileMenuToggle?: () => void;
}

export function Topbar({ onMobileMenuToggle }: TopbarProps) {
  return (
    <header className="bg-white border-b border-fintech-border sticky top-0 z-10 h-16 shrink-0">
      <div className="h-full px-4 md:px-6 flex items-center justify-between">
        {/* Left: Hamburger (Mobile Only) & Search */}
        <div className="flex items-center gap-3 flex-1">
          <button
            className="md:hidden p-2 -ml-2 text-fintech-muted hover:text-fintech-navy hover:bg-fintech-bg rounded-lg transition-colors focus:outline-none"
            onClick={onMobileMenuToggle}
            aria-label="Open menu"
          >
            <Menu className="w-5 h-5" />
          </button>

          <div className="relative w-full max-w-md hidden sm:block">
            <Search className="w-4 h-4 text-fintech-muted absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              placeholder="Search cases, payments..."
              className="w-full pl-9 pr-14 py-1.5 bg-fintech-bg border border-fintech-border rounded-lg text-sm text-fintech-navy placeholder:text-fintech-muted focus:outline-none focus:ring-1 focus:ring-fintech-blue transition-all"
            />
            <div className="absolute right-2.5 top-1/2 -translate-y-1/2 text-[10px] text-fintech-muted font-medium bg-white px-1.5 py-0.5 rounded border border-fintech-border shadow-xs">
              Ctrl K
            </div>
          </div>

          {/* Mobile search icon only */}
          <button className="sm:hidden p-2 text-fintech-muted hover:text-fintech-navy hover:bg-fintech-bg rounded-lg transition-colors">
            <Search className="w-5 h-5" />
          </button>
        </div>

        {/* Right: Date range & Merchant selector */}
        <div className="flex items-center gap-2 md:gap-3 shrink-0">
          <button className="hidden md:flex items-center gap-2 text-xs font-medium text-fintech-navy bg-fintech-bg hover:bg-slate-100 border border-fintech-border px-3 py-1.5 rounded-lg transition-colors">
            <Calendar className="w-3.5 h-3.5 text-fintech-muted" />
            <span>Last 30 days</span>
            <ChevronDown className="w-3 h-3 text-fintech-muted ml-0.5" />
          </button>

          <div className="hidden md:block h-5 w-px bg-fintech-border mx-1"></div>

          <button className="flex items-center gap-2 md:gap-2.5 hover:bg-fintech-bg p-1.5 md:px-2.5 md:py-1.5 rounded-lg transition-colors border border-transparent hover:border-fintech-border">
            <div className="w-7 h-7 rounded-full bg-fintech-sidebar flex items-center justify-center text-white text-xs font-bold">
              A
            </div>
            <div className="hidden md:flex flex-col items-start text-left">
              <span className="text-xs font-semibold text-fintech-navy leading-none">Acme Payments</span>
              <span className="text-[10px] text-fintech-muted mt-0.5 leading-none">merchant_demo</span>
            </div>
            <ChevronDown className="w-3 h-3 text-fintech-muted ml-1" />
          </button>
        </div>
      </div>
    </header>
  );
}
