import React, { ReactNode } from 'react';
import { cn } from '@/lib/utils';

interface CardProps {
    children: ReactNode;
    className?: string;
    hover?: boolean;
    glass?: boolean;
}

export default function Card({ children, className, hover = false, glass = true }: CardProps) {
    return (
        <div
            className={cn(
                'rounded-xl p-6',
                glass ? 'glass-dark' : 'bg-dark-800 border border-dark-700',
                hover && 'hover:scale-[1.02] hover:shadow-glass-lg transition-all duration-300 cursor-pointer',
                className
            )}
        >
            {children}
        </div>
    );
}
