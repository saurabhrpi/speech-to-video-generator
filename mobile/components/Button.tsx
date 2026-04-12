import { forwardRef, useCallback } from 'react';
import { Text, type PressableProps } from 'react-native';
import Animated, {
  useSharedValue,
  useAnimatedStyle,
  withSpring,
} from 'react-native-reanimated';
import * as Haptics from 'expo-haptics';
import { cva, type VariantProps } from 'class-variance-authority';
import { cn } from '@/lib/utils';

const AnimatedPressable = Animated.createAnimatedComponent(
  require('react-native').Pressable,
);

const buttonVariants = cva(
  'flex-row items-center justify-center rounded-button',
  {
    variants: {
      variant: {
        default: 'bg-primary border border-white/[0.18]',
        secondary: 'bg-secondary border border-white/[0.12]',
        destructive: 'bg-destructive',
        outline: 'border border-white/[0.18] bg-background',
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
    const scale = useSharedValue(1);
    const animatedStyle = useAnimatedStyle(() => ({
      transform: [{ scale: scale.value }],
      opacity: scale.value < 1 ? 0.9 : 1,
    }));

    const handlePressIn = useCallback(() => {
      if (!disabled) scale.value = withSpring(0.96, { damping: 15, stiffness: 300 });
    }, [disabled, scale]);

    const handlePressOut = useCallback(() => {
      scale.value = withSpring(1, { damping: 15, stiffness: 300 });
    }, [scale]);

    const handlePress = (e: any) => {
      if (!disabled) {
        Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
      }
      onPress?.(e);
    };

    return (
      <AnimatedPressable
        ref={ref}
        className={cn(
          buttonVariants({ variant, size }),
          disabled && 'opacity-50',
          className,
        )}
        style={animatedStyle}
        disabled={disabled}
        onPressIn={handlePressIn}
        onPressOut={handlePressOut}
        onPress={handlePress}
        {...props}
      >
        {children ?? (
          <Text className={cn(textVariants({ variant }), textClassName)}>
            {title}
          </Text>
        )}
      </AnimatedPressable>
    );
  },
);

Button.displayName = 'Button';
