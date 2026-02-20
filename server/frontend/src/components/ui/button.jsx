import { forwardRef } from "react";
import { cn } from "../../lib/utils";

const buttonVariants = {
  variant: {
    default:
      "bg-sky-500 text-white hover:bg-sky-600 border-sky-500",
    destructive:
      "bg-red-600 text-white hover:bg-red-700 border-red-600",
    outline:
      "border border-slate-300 bg-transparent hover:bg-slate-100 text-slate-700 dark:border-slate-600 dark:hover:bg-slate-800 dark:text-slate-200",
    ghost: "hover:bg-slate-100 text-slate-700 dark:hover:bg-slate-800 dark:text-slate-200",
  },
  size: {
    sm: "h-8 px-3 text-sm",
    default: "h-10 px-4",
    lg: "h-11 px-8",
  },
};

export const Button = forwardRef(
  ({ className, variant = "default", size = "default", ...props }, ref) => (
    <button
      ref={ref}
      className={cn(
        "inline-flex items-center justify-center rounded-md border font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-sky-500 focus-visible:ring-offset-2 focus-visible:ring-offset-white dark:focus-visible:ring-offset-slate-950 disabled:pointer-events-none disabled:opacity-50",
        buttonVariants.variant[variant],
        buttonVariants.size[size],
        className
      )}
      {...props}
    />
  )
);
Button.displayName = "Button";
