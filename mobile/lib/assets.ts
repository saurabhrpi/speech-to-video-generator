/**
 * Asset registry — central place to swap UI image assets without touching
 * components or callers.
 *
 * Each export is a Metro-bundled asset reference (the return value of
 * `require()`). To change an icon: drop the new file under
 * `mobile/assets/images/` and update the require path here. CoinIcon and
 * similar wrappers consume these constants instead of inlining `require()`.
 */

export const COIN_ICON_SOURCE = require('@/assets/images/Coin.png');
