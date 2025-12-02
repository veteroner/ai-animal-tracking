'use client';

import { LucideIcon } from 'lucide-react';
import { TrendingUp, TrendingDown } from 'lucide-react';

interface StatCardProps {
  title: string;
  value: string | number;
  change?: number;
  changeLabel?: string;
  icon: LucideIcon;
  iconBg?: string;
  iconColor?: string;
}

export default function StatCard({
  title,
  value,
  change,
  changeLabel,
  icon: Icon,
  iconBg = 'bg-primary-100',
  iconColor = 'text-primary-600',
}: StatCardProps) {
  const isPositive = change && change > 0;
  
  return (
    <div className="card-hover">
      <div className="flex items-start justify-between">
        <div className={`p-3 rounded-xl ${iconBg}`}>
          <Icon className={`w-6 h-6 ${iconColor}`} />
        </div>
        {change !== undefined && (
          <div className={`flex items-center gap-1 ${isPositive ? 'stat-change-up' : 'stat-change-down'}`}>
            {isPositive ? (
              <TrendingUp className="w-4 h-4" />
            ) : (
              <TrendingDown className="w-4 h-4" />
            )}
            <span>{Math.abs(change)}%</span>
          </div>
        )}
      </div>
      <div className="mt-4">
        <p className="stat-value">{value}</p>
        <p className="stat-label">{title}</p>
        {changeLabel && (
          <p className="text-xs text-gray-400 mt-1">{changeLabel}</p>
        )}
      </div>
    </div>
  );
}
