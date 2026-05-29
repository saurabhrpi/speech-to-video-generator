import { Image, type ImageStyle, type StyleProp } from 'react-native';
import { COIN_ICON_SOURCE } from '@/lib/assets';

interface CoinIconProps {
  size?: number;
  style?: StyleProp<ImageStyle>;
}

export default function CoinIcon({ size = 14, style }: CoinIconProps) {
  return (
    <Image
      source={COIN_ICON_SOURCE}
      style={[{ width: size, height: size, resizeMode: 'contain' }, style]}
      accessibilityLabel="coin"
    />
  );
}
