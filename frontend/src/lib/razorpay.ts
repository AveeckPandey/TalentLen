"use client";

import { createRazorpayOrder, verifyRazorpayPayment } from "./api";
import type { PlanTier, UserQuota } from "./types";

/**
 * Dynamically loads the official Razorpay Checkout SDK script if not already present in the DOM.
 */
export function loadRazorpayScript(): Promise<boolean> {
  return new Promise((resolve) => {
    if (typeof window === "undefined") {
      resolve(false);
      return;
    }
    if ((window as any).Razorpay) {
      resolve(true);
      return;
    }
    const existingScript = document.getElementById("razorpay-checkout-script");
    if (existingScript) {
      resolve(true);
      return;
    }

    const script = document.createElement("script");
    script.id = "razorpay-checkout-script";
    script.src = "https://checkout.razorpay.com/v1/checkout.js";
    script.async = true;
    script.onload = () => resolve(true);
    script.onerror = () => {
      console.error("Failed to load Razorpay SDK");
      resolve(false);
    };
    document.body.appendChild(script);
  });
}

export interface OpenCheckoutArgs {
  tier: PlanTier;
  userEmail?: string | null;
  onSuccess: (updatedQuota: UserQuota) => void;
  onError?: (error: Error) => void;
}

/**
 * Initiates Razorpay test checkout flow:
 * 1. Loads script
 * 2. Creates order on backend
 * 3. Opens Razorpay popup
 * 4. Verifies payment signature on backend
 */
export async function openRazorpayCheckout({
  tier,
  userEmail,
  onSuccess,
  onError,
}: OpenCheckoutArgs): Promise<void> {
  try {
    const loaded = await loadRazorpayScript();
    if (!loaded) {
      throw new Error("Razorpay SDK could not be loaded. Please check your internet connection.");
    }

    // 1. Create order on FastAPI backend
    const order = await createRazorpayOrder(tier, "INR");

    // 2. Configure Razorpay modal
    const options = {
      key: order.key_id || process.env.NEXT_PUBLIC_RAZORPAY_KEY_ID || "rzp_test_To5J8S6PiLcb1j",
      amount: order.amount,
      currency: order.currency,
      name: "TalentLens AI",
      description: `Upgrade to ${order.tier_name}`,
      order_id: order.order_id,
      handler: async (response: {
        razorpay_order_id: string;
        razorpay_payment_id: string;
        razorpay_signature: string;
      }) => {
        try {
          // 3. Verify signature on backend
          const verification = await verifyRazorpayPayment(
            response.razorpay_order_id,
            response.razorpay_payment_id,
            response.razorpay_signature,
            tier
          );
          onSuccess(verification.quota);
        } catch (verifErr: any) {
          if (onError) onError(verifErr);
          else alert(`Payment verification failed: ${verifErr.message}`);
        }
      },
      prefill: {
        email: userEmail || "candidate@talentlens.io",
      },
      theme: {
        color: "#0066FF",
      },
      modal: {
        ondismiss: () => {
          console.log("Razorpay checkout modal dismissed by user");
        },
      },
    };

    const rzp = new (window as any).Razorpay(options);
    rzp.on("payment.failed", function (response: any) {
      const err = new Error(response.error?.description || "Payment failed or cancelled.");
      if (onError) onError(err);
      else alert(`Payment Failed: ${err.message}`);
    });

    rzp.open();
  } catch (err: any) {
    if (onError) onError(err);
    else alert(`Checkout error: ${err.message}`);
  }
}
