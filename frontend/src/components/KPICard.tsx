import type { LucideIcon } from 'lucide-react';

interface KPICardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  icon: LucideIcon;
  bgColor?: string; // pastel background color e.g. '#F3F0FF', '#D9F3E4', '#DCEBFA', '#FFE7D2', '#F8DDE8'
  iconColor?: string;
}

export const KPICard: React.FC<KPICardProps> = ({
  title,
  value,
  subtitle,
  icon: Icon,
  bgColor = '#F3F0FF',
  iconColor = '#8B7CF6'
}) => {
  return (
    <div className="bg-white rounded-2xl border border-[#EAE7F2] p-5 shadow-xs hover:shadow-md transition-all duration-200">
      <div className="flex items-start justify-between">
        <div>
          <span className="text-xs font-medium text-[#77748C] tracking-wide uppercase">{title}</span>
          <h3 className="text-2xl font-bold text-[#29263D] mt-1">{value}</h3>
          {subtitle && (
            <p className="text-xs text-[#77748C] mt-1 flex items-center gap-1 font-medium">
              {subtitle}
            </p>
          )}
        </div>
        <div
          className="w-12 h-12 rounded-2xl flex items-center justify-center transition-transform hover:scale-105"
          style={{ backgroundColor: bgColor }}
        >
          <Icon className="w-6 h-6" style={{ color: iconColor }} />
        </div>
      </div>
    </div>
  );
};
