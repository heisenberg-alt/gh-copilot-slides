'use client';

import { signOut } from 'next-auth/react';
import { Sparkles, LogOut, User } from 'lucide-react';

interface HeaderProps {
  user?: {
    name?: string | null;
    email?: string | null;
    image?: string | null;
  };
}

export function Header({ user }: HeaderProps) {
  return (
    <header className="sticky top-0 z-40 h-16 bg-background/80 backdrop-blur-xl border-b border-border">
      <div className="h-full px-6 flex items-center justify-between">
        {/* Logo */}
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-apple bg-accent flex items-center justify-center">
            <Sparkles className="w-4 h-4 text-white" />
          </div>
          <span className="font-semibold text-lg hidden sm:block">Slide Builder</span>
        </div>

        {/* User menu */}
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-full bg-surface flex items-center justify-center">
              {user?.image ? (
                <img
                  src={user.image}
                  alt={user.name || 'User'}
                  className="w-8 h-8 rounded-full"
                />
              ) : (
                <User className="w-4 h-4 text-text-secondary" />
              )}
            </div>
            <div className="hidden sm:block">
              <p className="text-sm font-medium">{user?.name || 'User'}</p>
              <p className="text-xs text-text-secondary">{user?.email}</p>
            </div>
          </div>

          <button
            onClick={() => signOut({ callbackUrl: '/' })}
            className="btn btn-ghost p-2"
            title="Sign out"
          >
            <LogOut className="w-4 h-4" />
          </button>
        </div>
      </div>
    </header>
  );
}
