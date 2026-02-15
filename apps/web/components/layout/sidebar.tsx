'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { Home, Plus, Settings, Menu, X } from 'lucide-react';
import { useState } from 'react';
import { cn } from '@/lib/cn';

const navItems = [
  { href: '/', icon: Home, label: 'Dashboard' },
  { href: '/new', icon: Plus, label: 'New Presentation' },
  { href: '/settings', icon: Settings, label: 'Settings' },
];

export function Sidebar() {
  const pathname = usePathname();
  const [isOpen, setIsOpen] = useState(false);

  return (
    <>
      {/* Mobile toggle */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="fixed bottom-6 right-6 z-50 lg:hidden btn btn-primary w-14 h-14 rounded-full shadow-[0_8px_28px_rgba(0,0,0,0.12),0_2px_4px_rgba(0,0,0,0.08)]"
        aria-label={isOpen ? 'Close navigation menu' : 'Open navigation menu'}
        aria-expanded={isOpen}
        aria-controls="sidebar-nav"
      >
        {isOpen ? (
          <X className="w-6 h-6" aria-hidden="true" />
        ) : (
          <Menu className="w-6 h-6" aria-hidden="true" />
        )}
      </button>

      {/* Mobile overlay */}
      {isOpen && (
        <div
          className="fixed inset-0 bg-black/50 z-40 lg:hidden"
          onClick={() => setIsOpen(false)}
          aria-hidden="true"
        />
      )}

      {/* Sidebar */}
      <aside
        id="sidebar-nav"
        className={cn(
          'fixed top-16 left-0 bottom-0 w-64 bg-background border-r z-40',
          'transition-transform duration-300',
          'lg:translate-x-0',
          isOpen ? 'translate-x-0' : '-translate-x-full'
        )}
        style={{ borderColor: 'var(--border)' }}
        role="navigation"
        aria-label="Main navigation"
      >
        <nav className="p-4 space-y-2">
          {navItems.map((item) => {
            const isActive =
              pathname === item.href ||
              (item.href !== '/' && pathname.startsWith(item.href));

            return (
              <Link
                key={item.href}
                href={item.href}
                onClick={() => setIsOpen(false)}
                className={cn(
                  'flex items-center gap-3 px-4 py-3 rounded-[12px] text-sm font-medium',
                  'transition-all duration-200',
                  isActive
                    ? 'bg-accent text-white'
                    : 'text-text-secondary hover:bg-surface hover:text-text-primary'
                )}
                aria-current={isActive ? 'page' : undefined}
              >
                <item.icon className="w-5 h-5" aria-hidden="true" />
                {item.label}
              </Link>
            );
          })}
        </nav>
      </aside>
    </>
  );
}
