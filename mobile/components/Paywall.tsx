import { useEffect, useState } from 'react';
import {
  Modal,
  View,
  Text,
  Pressable,
  ScrollView,
  ActivityIndicator,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import * as WebBrowser from 'expo-web-browser';
import Purchases, {
  type PurchasesOffering,
  type PurchasesPackage,
} from 'react-native-purchases';

import { Button } from '@/components/Button';
import { useAuthStore } from '@/store/auth-store';
import { Colors } from '@/lib/design-tokens';
import {
  PRIVACY_URL,
  PRO_PACK_COUNT,
  TERMS_URL,
} from '@/lib/constants';

const BULLETS = [
  'Hyper-realistic, film-crew quality renders',
  'TikTok & Instagram-ready exports',
  'No watermark',
  'New styles & room types added regularly',
];

export default function Paywall() {
  const paywallOpen = useAuthStore((s) => s.paywallOpen);
  const closePaywall = useAuthStore((s) => s.closePaywall);
  const isAnonymous = useAuthStore((s) => s.isAnonymous);
  const signInWithApple = useAuthStore((s) => s.signInWithApple);
  const refreshUsage = useAuthStore((s) => s.refreshUsage);

  const [offering, setOffering] = useState<PurchasesOffering | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [purchasing, setPurchasing] = useState(false);
  const [purchaseError, setPurchaseError] = useState<string | null>(null);

  useEffect(() => {
    if (!paywallOpen) return;
    let cancelled = false;
    setLoadError(null);
    setPurchaseError(null);
    Purchases.getOfferings()
      .then((result) => {
        if (cancelled) return;
        const current = result.current;
        if (!current || current.availablePackages.length === 0) {
          setLoadError('No offerings available. Please try again later.');
          setOffering(null);
          return;
        }
        setOffering(current);
      })
      .catch((e: any) => {
        if (cancelled) return;
        setLoadError(e?.message ?? 'Failed to load offering.');
      });
    return () => {
      cancelled = true;
    };
  }, [paywallOpen]);

  const pkg: PurchasesPackage | null = offering?.availablePackages[0] ?? null;
  const priceString = pkg?.product.priceString;

  async function handlePurchase() {
    if (!pkg) return;
    setPurchasing(true);
    setPurchaseError(null);
    try {
      if (isAnonymous) {
        try {
          await signInWithApple();
        } catch (e: any) {
          if (e?.code === 'ERR_REQUEST_CANCELED') {
            return;
          }
          throw e;
        }
      }
      await Purchases.purchasePackage(pkg);
      await refreshUsage();
      closePaywall();
    } catch (e: any) {
      if (e?.userCancelled) {
        return;
      }
      setPurchaseError(e?.message ?? 'Purchase failed. Please try again.');
    } finally {
      setPurchasing(false);
    }
  }

  async function handleRestore() {
    setPurchasing(true);
    setPurchaseError(null);
    try {
      await Purchases.restorePurchases();
      await refreshUsage();
      closePaywall();
    } catch (e: any) {
      setPurchaseError(e?.message ?? 'Restore failed. Please try again.');
    } finally {
      setPurchasing(false);
    }
  }

  const ctaTitle = !pkg
    ? 'Loading…'
    : purchasing
    ? 'Processing…'
    : `Unlock Pro — ${PRO_PACK_COUNT} timelapses for ${priceString}`;

  return (
    <Modal
      visible={paywallOpen}
      animationType="slide"
      presentationStyle="fullScreen"
      onRequestClose={closePaywall}
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
          contentContainerClassName="px-6 pb-8 pt-4 gap-8"
          showsVerticalScrollIndicator={false}
        >
          <View className="gap-3">
            <Text className="text-heading font-heading text-foreground">
              Unlock Pro
            </Text>
            <Text className="text-body font-body text-muted-foreground">
              One-time purchase. No subscription.
            </Text>
          </View>

          <View className="gap-3">
            {BULLETS.map((b) => (
              <View key={b} className="flex-row items-start gap-3">
                <Text className="text-body font-body text-foreground">•</Text>
                <Text className="flex-1 text-body font-body text-foreground">
                  {b}
                </Text>
              </View>
            ))}
          </View>

          {loadError ? (
            <View className="rounded-card border border-destructive/50 bg-destructive/10 p-3">
              <Text className="text-body font-body text-destructive">
                {loadError}
              </Text>
            </View>
          ) : null}

          {purchaseError ? (
            <View className="rounded-card border border-destructive/50 bg-destructive/10 p-3">
              <Text className="text-body font-body text-destructive">
                {purchaseError}
              </Text>
            </View>
          ) : null}
        </ScrollView>

        <View className="gap-3 px-6 pb-6 pt-2">
          <Button
            size="lg"
            onPress={handlePurchase}
            disabled={!pkg || purchasing}
            title={ctaTitle}
            className="w-full"
          />

          {purchasing ? (
            <View className="items-center py-1">
              <ActivityIndicator color={Colors.textPrimary} />
            </View>
          ) : (
            <Pressable
              onPress={handleRestore}
              disabled={purchasing}
              hitSlop={8}
              accessibilityLabel="Restore purchases"
            >
              <Text className="text-center text-body font-body text-muted-foreground">
                Restore purchases
              </Text>
            </Pressable>
          )}

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
    </Modal>
  );
}
