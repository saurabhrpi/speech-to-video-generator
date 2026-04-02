import { forwardRef } from 'react';
import { Pressable, Text, type PressableProps } from 'react-native';
import * as Haptics from 'expo-haptics';
import { cva, type VariantProps } from 'class-variance-authority';
import { clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

function cn(...inputs: (string | undefined | null | false)[]) {
  return twMerge(clsx(inputs));
}

const buttonVariants = cva(
  'flex-row items-center justify-center rounded-md',
  {
    variants: {
      variant: {
        default: 'bg-primary',
        secondary: 'bg-secondary',
        destructive: 'bg-destructive',
        outline: 'border border-input bg-background',
        ghost: '',
      },
      size: {
        default: 'h-10 px-4 py-2',
        sm: 'h-9 px-3',
        lg: 'h-12 px-8',
        icon: 'h-10 w-10',
      },
    },
    defaultVariants: {
      variant: 'default',
      size: 'default',
    },
  },
);

const textVariants = cva('text-sm font-medium', {
  variants: {
    variant: {
      default: 'text-primary-foreground',
      secondary: 'text-secondary-foreground',
      destructive: 'text-destructive-foreground',
      outline: 'text-foreground',
      ghost: 'text-foreground',
    },
  },
  defaultVariants: {
    variant: 'default',
  },
});

interface ButtonProps extends PressableProps, VariantProps<typeof buttonVariants> {
  title?: string;
  children?: React.ReactNode;
  className?: string;
  textClassName?: string;
}

export const Button = forwardRef<any, ButtonProps>(
  ({ variant, size, title, children, className, textClassName, disabled, onPress, ...props }, ref) => {
    const handlePress = (e: any) => {
      if (!disabled) {
        Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
      }
      onPress?.(e);
    };

    return (
      <Pressable
        ref={ref}
        className={cn(
          buttonVariants({ variant, size }),
          disabled && 'opacity-50',
          className,
        )}
        disabled={disabled}
        onPress={handlePress}
        {...props}
      >
        {children ?? (
          <Text className={cn(textVariants({ variant }), textClassName)}>
            {title}
          </Text>
        )}
      </Pressable>
    );
  },
);

Button.displayName = 'Button';
