import React from 'react';
import { cn, getStatusBadgeClass } from '@/lib/utils';

interface BadgeProps {
    children: React.ReactNode;
    variant?: 'default' | 'status';
    status?: string;
    className?: string;
}

export default function Badge({ children, variant = 'default', status, className }: BadgeProps) {
    if (variant === 'status' && status) {
        return (
            <span
                className={cn(
                    'inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border',
                    getStatusBadgeClass(status),
                    className
                )}
            >
                {children}
            </span>
        );
    }

    return (
        <span
            className={cn(
                'inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium',
                'bg-primary-500/20 text-primary-300 border border-primary-500/30',
                className
            )}
        >
            {children}
        </span>
    );
}
