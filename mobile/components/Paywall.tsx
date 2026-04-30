import { useEffect, useMemo, useState } from 'react';
import {
  View,
  Text,
  Pressable,
  ScrollView,
  ActivityIndicator,
  useWindowDimensions,
} from 'react-native';
import Animated, {
  useAnimatedStyle,
  useSharedValue,
  withTiming,
} from 'react-native-reanimated';
import { SafeAreaView } from 'react-native-safe-area-context';
import * as WebBrowser from 'expo-web-browser';
import Purchases, {
  type PurchasesOffering,
  type PurchasesPackage,
} from 'react-native-purchases';

import { Button } from '@/components/Button';
import { grantCreditsForTransaction } from '@/lib/purchases';
import { useAuthStore } from '@/store/auth-store';
import { Colors } from '@/lib/design-tokens';
import {
  BEST_VALUE_PACK,
  DEFAULT_SELECTED_PACK,
  PACK_CREDITS,
  PACK_SKUS,
  PRIVACY_URL,
  TERMS_URL,
  type PackSku,
} from '@/lib/constants';

type PackageMap = Record<PackSku, PurchasesPackage>;

function formatUnit(price: number, currencyCode: string, credits: number): string {
  const per = price / credits;
  try {
    return new Intl.NumberFormat(undefined, {
      style: 'currency',
      currency: currencyCode,
      minimumFractionDigits: 2,
      maximumFractionDigits: 3,
    }).format(per);
  } catch {
    return `${currencyCode} ${per.toFixed(3)}`;
  }
}

export default function Paywall() {
  const paywallOpen = useAuthStore((s) => s.paywallOpen);
  const closePaywall = useAuthStore((s) => s.closePaywall);
  const isAnonymous = useAuthStore((s) => s.isAnonymous);
  const signInWithApple = useAuthStore((s) => s.signInWithApple);
  const refreshCredits = useAuthStore((s) => s.refreshCredits);

  const [packages, setPackages] = useState<PackageMap | null>(null);
  const [selectedSku, setSelectedSku] = useState<PackSku>(DEFAULT_SELECTED_PACK);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [purchasing, setPurchasing] = useState(false);
  const [purchaseError, setPurchaseError] = useState<string | null>(null);

  useEffect(() => {
    if (!paywallOpen) return;
    let cancelled = false;
    setLoadError(null);
    setPurchaseError(null);
    setPackages(null);
    setSelectedSku(DEFAULT_SELECTED_PACK);

    Purchases.getOfferings()
      .then((result) => {
        if (cancelled) return;
        const current: PurchasesOffering | null = result.current ?? null;
        if (!current) {
          setLoadError('No offerings available. Please try again later.');
          return;
        }
        const map: Partial<PackageMap> = {};
        for (const pkg of current.availablePackages) {
          const id = pkg.identifier as PackSku;
          if (PACK_SKUS.includes(id)) map[id] = pkg;
        }
        const missing = PACK_SKUS.filter((s) => !map[s]);
        if (missing.length > 0) {
          setLoadError(`Missing packs: ${missing.join(', ')}.`);
          return;
        }
        setPackages(map as PackageMap);
      })
      .catch((e: any) => {
        if (cancelled) return;
        setLoadError(e?.message ?? 'Failed to load offering.');
      });

    return () => {
      cancelled = true;
    };
  }, [paywallOpen]);

  const selectedPkg = packages?.[selectedSku] ?? null;

  const ctaTitle = useMemo(() => {
    if (purchasing) return 'Processing…';
    if (!selectedPkg) return 'Loading…';
    return `Buy ${PACK_CREDITS[selectedSku]} credits — ${selectedPkg.product.priceString}`;
  }, [purchasing, selectedPkg, selectedSku]);

  async function handlePurchase() {
    if (!selectedPkg) return;
    setPurchasing(true);
    setPurchaseError(null);
    try {
      if (isAnonymous) {
        try {
          await signInWithApple();
        } catch (e: any) {
          if (e?.code === 'ERR_REQUEST_CANCELED') return;
          throw e;
        }
      }
      const res = await Purchases.purchasePackage(selectedPkg);
      const txId = res.transaction?.transactionIdentifier;
      if (!txId) {
        setPurchaseError(
          'Purchase succeeded but could not be confirmed. If credits do not appear, please email support@speech-2-video.ai.',
        );
        return;
      }
      try {
        await grantCreditsForTransaction(selectedPkg.identifier, txId);
        await refreshCredits();
        closePaywall();
      } catch {
        await refreshCredits();
        setPurchaseError(
          'Credits should appear shortly. If not, please email support@speech-2-video.ai.',
        );
      }
    } catch (e: any) {
      if (e?.userCancelled) return;
      setPurchaseError(e?.message ?? 'Purchase failed. Please try again.');
    } finally {
      setPurchasing(false);
    }
  }

  // Refactored off <Modal> to a root-level Animated.View overlay because iOS Modal
  // (even transparent) leaves the Paywall's touch focus stuck after a stacked sheet
  // (Apple Sign In, IAP) dismisses — symptom: X unresponsive, drag-handle cursor.
  // Same View tree as the rest of the app means no separate window, no focus restoration.
  const { height: screenHeight } = useWindowDimensions();
  const slideY = useSharedValue(screenHeight);
  useEffect(() => {
    slideY.value = withTiming(paywallOpen ? 0 : screenHeight, { duration: 280 });
  }, [paywallOpen, screenHeight, slideY]);
  const overlayStyle = useAnimatedStyle(() => ({
    transform: [{ translateY: slideY.value }],
  }));

  return (
    <Animated.View
      pointerEvents={paywallOpen ? 'auto' : 'none'}
      style={[
        {
          position: 'absolute',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          zIndex: 1000,
          elevation: 1000,
          backgroundColor: Colors.background,
        },
        overlayStyle,
      ]}
    >
      <SafeAreaView style={{ flex: 1, backgroundColor: Colors.background }}>
        <View className="flex-row items-center justify-end px-5 pt-2">
          <Pressable
            onPress={closePaywall}
            hitSlop={12}
            accessibilityLabel="Close"
          >
            <Text className="text-subheading font-body text-muted-foreground">×</Text>
          </Pressable>
        </View>

        <ScrollView
          className="flex-1"
          contentContainerClassName="px-6 pb-8 pt-4 gap-6"
          showsVerticalScrollIndicator={false}
        >
          <View className="gap-2">
            <Text className="text-heading font-body-medium text-foreground">Buy Credits</Text>
            <Text className="text-body font-body text-muted-foreground">
              One-time purchase. Credits never expire.
            </Text>
          </View>

          <View className="gap-3">
            {PACK_SKUS.map((sku) => {
              const pkg = packages?.[sku];
              const selected = selectedSku === sku;
              const isBest = sku === BEST_VALUE_PACK;
              const credits = PACK_CREDITS[sku];
              return (
                <Pressable
                  key={sku}
                  onPress={() => setSelectedSku(sku)}
                  disabled={!pkg}
                  accessibilityRole="radio"
                  accessibilityState={{ selected }}
                  style={{
                    borderWidth: 2,
                    borderColor: selected ? Colors.textPrimary : Colors.border,
                    backgroundColor: Colors.card,
                    opacity: pkg ? 1 : 0.5,
                  }}
                  className="rounded-card p-4"
                >
                  {isBest ? (
                    <View
                      style={{ backgroundColor: Colors.textPrimary, alignSelf: 'flex-start' }}
                      className="mb-2 rounded-full px-2 py-0.5"
                    >
                      <Text
                        style={{ color: Colors.background }}
                        className="text-caption font-body"
                      >
                        Best value
                      </Text>
                    </View>
                  ) : null}
                  <View className="flex-row items-center justify-between">
                    <Text className="text-subheading font-body-medium text-foreground">
                      {credits} credits
                    </Text>
                    <Text className="text-subheading font-body-medium text-foreground">
                      {pkg?.product.priceString ?? '—'}
                    </Text>
                  </View>
                  <View className="mt-1 flex-row items-center justify-end">
                    <Text className="text-caption font-body text-muted-foreground">
                      {pkg
                        ? `${formatUnit(pkg.product.price, pkg.product.currencyCode, credits)} / credit`
                        : ' '}
                    </Text>
                  </View>
                </Pressable>
              );
            })}
          </View>

          {loadError ? (
            <View className="rounded-card border border-destructive/50 bg-destructive/10 p-3">
              <Text className="text-body font-body text-destructive">{loadError}</Text>
            </View>
          ) : null}

          {purchaseError ? (
            <View className="rounded-card border border-destructive/50 bg-destructive/10 p-3">
              <Text className="text-body font-body text-destructive">{purchaseError}</Text>
            </View>
          ) : null}
        </ScrollView>

        <View className="gap-3 px-6 pb-6 pt-2">
          <Button
            size="lg"
            onPress={handlePurchase}
            disabled={!selectedPkg || purchasing}
            title={ctaTitle}
            className="w-full"
          />

          {purchasing ? (
            <View className="items-center py-1">
              <ActivityIndicator color={Colors.textPrimary} />
            </View>
          ) : null}

          <View className="flex-row items-center justify-center gap-4 pt-1">
            <Pressable
              onPress={() => WebBrowser.openBrowserAsync(TERMS_URL)}
              hitSlop={8}
            >
              <Text className="text-caption font-body text-muted-foreground">
                Terms of Use
              </Text>
            </Pressable>
            <Text className="text-caption text-muted-foreground">·</Text>
            <Pressable
              onPress={() => WebBrowser.openBrowserAsync(PRIVACY_URL)}
              hitSlop={8}
            >
              <Text className="text-caption font-body text-muted-foreground">
                Privacy Policy
              </Text>
            </Pressable>
          </View>
        </View>
      </SafeAreaView>
    </Animated.View>
  );
}
