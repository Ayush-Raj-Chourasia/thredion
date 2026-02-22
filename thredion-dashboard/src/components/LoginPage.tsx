"use client";

import { useState, useRef, useEffect } from "react";
import { Brain, Phone, ArrowRight, Loader2, ShieldCheck, MessageCircle } from "lucide-react";
import { sendOTP, verifyOTP } from "@/lib/api";
import { useAuth } from "@/components/AuthProvider";

type Step = "phone" | "otp";

export default function LoginPage() {
  const { login } = useAuth();
  const [step, setStep] = useState<Step>("phone");
  const [phone, setPhone] = useState("");
  const [otp, setOtp] = useState(["", "", "", "", "", ""]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [countdown, setCountdown] = useState(0);
  const otpRefs = useRef<(HTMLInputElement | null)[]>([]);

  // Countdown timer for resend
  useEffect(() => {
    if (countdown <= 0) return;
    const t = setTimeout(() => setCountdown((c) => c - 1), 1000);
    return () => clearTimeout(t);
  }, [countdown]);

  // ── Send OTP ──────────────────────────────────────────
  const handleSendOTP = async () => {
    const cleaned = phone.replace(/[\s\-\(\)]/g, "");
    if (cleaned.length < 8) {
      setError("Enter a valid phone number with country code (e.g. +91...)");
      return;
    }
    setLoading(true);
    setError("");
    try {
      const result = await sendOTP(cleaned.startsWith("+") ? cleaned : `+${cleaned}`);
      setStep("otp");
      setCountdown(Math.floor(result.expires_in_seconds || 300));
      setTimeout(() => otpRefs.current[0]?.focus(), 100);
    } catch (err: any) {
      const msg = err.message || "Failed to send OTP";
      // Try to extract detail from API error
      try {
        const parsed = JSON.parse(msg.replace(/^API \d+: /, ""));
        setError(parsed.detail || msg);
      } catch {
        setError(msg);
      }
    } finally {
      setLoading(false);
    }
  };

  // ── OTP input handling ────────────────────────────────
  const handleOtpChange = (index: number, value: string) => {
    if (!/^\d*$/.test(value)) return; // digits only
    const next = [...otp];
    next[index] = value.slice(-1);
    setOtp(next);
    if (value && index < 5) {
      otpRefs.current[index + 1]?.focus();
    }
  };

  const handleOtpKeyDown = (index: number, e: React.KeyboardEvent) => {
    if (e.key === "Backspace" && !otp[index] && index > 0) {
      otpRefs.current[index - 1]?.focus();
    }
    if (e.key === "Enter") {
      handleVerifyOTP();
    }
  };

  const handleOtpPaste = (e: React.ClipboardEvent) => {
    const text = e.clipboardData.getData("text").replace(/\D/g, "").slice(0, 6);
    if (text.length === 6) {
      e.preventDefault();
      setOtp(text.split(""));
      otpRefs.current[5]?.focus();
    }
  };

  // ── Verify OTP ────────────────────────────────────────
  const handleVerifyOTP = async () => {
    const code = otp.join("");
    if (code.length !== 6) {
      setError("Enter the complete 6-digit code");
      return;
    }
    setLoading(true);
    setError("");
    try {
      const cleaned = phone.replace(/[\s\-\(\)]/g, "");
      const result = await verifyOTP(cleaned.startsWith("+") ? cleaned : `+${cleaned}`, code);
      login(result.token, result.user);
    } catch (err: any) {
      const msg = err.message || "Invalid OTP";
      try {
        const parsed = JSON.parse(msg.replace(/^API \d+: /, ""));
        setError(parsed.detail || msg);
      } catch {
        setError(msg);
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-surface-50 dark:bg-gray-950 flex flex-col items-center justify-center px-4">
      {/* Background decoration */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-brand-100 dark:bg-brand-900/20 rounded-full blur-3xl opacity-30" />
        <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-purple-100 dark:bg-purple-900/20 rounded-full blur-3xl opacity-30" />
      </div>

      <div className="relative z-10 w-full max-w-md">
        {/* Logo */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-gradient-to-br from-brand-500 to-brand-700 shadow-lg shadow-brand-200 mb-4">
            <Brain className="h-8 w-8 text-white" />
          </div>
          <h1 className="text-2xl font-bold text-surface-900 dark:text-white">Thredion</h1>
          <p className="text-sm text-surface-500 dark:text-gray-400 mt-1">AI Cognitive Memory Engine</p>
        </div>

        {/* Card */}
        <div className="bg-white dark:bg-gray-900 rounded-2xl shadow-xl shadow-surface-200/50 dark:shadow-gray-950/50 border border-surface-200 dark:border-gray-700/50 p-8">
          {step === "phone" ? (
            <>
              <div className="flex items-center gap-3 mb-6">
                <div className="flex items-center justify-center w-10 h-10 rounded-xl bg-green-50 dark:bg-green-900/30">
                  <MessageCircle className="h-5 w-5 text-green-600 dark:text-green-400" />
                </div>
                <div>
                  <h2 className="text-lg font-semibold text-surface-900 dark:text-white">Login via WhatsApp</h2>
                  <p className="text-xs text-surface-500 dark:text-gray-400">We&apos;ll send you a verification code</p>
                </div>
              </div>

              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-surface-700 dark:text-gray-300 mb-1.5">
                    Phone Number
                  </label>
                  <div className="relative">
                    <Phone className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-surface-400 dark:text-gray-500" />
                    <input
                      type="tel"
                      value={phone}
                      onChange={(e) => {
                        setPhone(e.target.value);
                        setError("");
                      }}
                      onKeyDown={(e) => e.key === "Enter" && handleSendOTP()}
                      placeholder="+91 12345 67890"
                      className="w-full pl-10 pr-4 py-3 rounded-xl border border-surface-300 dark:border-gray-600 bg-surface-50 dark:bg-gray-800 text-surface-900 dark:text-white placeholder:text-surface-400 dark:placeholder:text-gray-500 focus:outline-none focus:border-brand-400 focus:ring-2 focus:ring-brand-100 dark:focus:ring-brand-800 transition-all"
                      autoFocus
                    />
                  </div>
                  <p className="text-xs text-surface-400 dark:text-gray-500 mt-1.5">
                    Use the same number you send WhatsApp links from
                  </p>
                </div>

                {error && (
                  <p className="text-sm text-red-600 dark:text-red-400 bg-red-50 dark:bg-red-950/30 rounded-lg px-3 py-2">{error}</p>
                )}

                <button
                  onClick={handleSendOTP}
                  disabled={loading || !phone.trim()}
                  className="w-full flex items-center justify-center gap-2 py-3 rounded-xl bg-gradient-to-r from-brand-600 to-brand-700 text-white font-medium shadow-md shadow-brand-200 hover:shadow-lg hover:shadow-brand-300 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
                >
                  {loading ? (
                    <Loader2 className="h-5 w-5 animate-spin" />
                  ) : (
                    <>
                      Send OTP
                      <ArrowRight className="h-4 w-4" />
                    </>
                  )}
                </button>
              </div>
            </>
          ) : (
            <>
              <div className="flex items-center gap-3 mb-6">
                <div className="flex items-center justify-center w-10 h-10 rounded-xl bg-brand-50 dark:bg-brand-900/30">
                  <ShieldCheck className="h-5 w-5 text-brand-600 dark:text-brand-400" />
                </div>
                <div>
                  <h2 className="text-lg font-semibold text-surface-900 dark:text-white">Enter Verification Code</h2>
                  <p className="text-xs text-surface-500 dark:text-gray-400">
                    Sent to <span className="font-medium text-surface-700 dark:text-gray-300">{phone}</span> on WhatsApp
                  </p>
                </div>
              </div>

              <div className="space-y-4">
                {/* OTP input boxes */}
                <div className="flex gap-2 justify-center" onPaste={handleOtpPaste}>
                  {otp.map((digit, i) => (
                    <input
                      key={i}
                      ref={(el) => { otpRefs.current[i] = el; }}
                      type="text"
                      inputMode="numeric"
                      maxLength={1}
                      value={digit}
                      aria-label={`OTP digit ${i + 1}`}
                      onChange={(e) => handleOtpChange(i, e.target.value)}
                      onKeyDown={(e) => handleOtpKeyDown(i, e)}
                      className="w-12 h-14 text-center text-xl font-bold rounded-xl border border-surface-300 dark:border-gray-600 bg-surface-50 dark:bg-gray-800 text-surface-900 dark:text-white focus:outline-none focus:border-brand-400 focus:ring-2 focus:ring-brand-100 dark:focus:ring-brand-800 transition-all"
                    />
                  ))}
                </div>

                {error && (
                  <p className="text-sm text-red-600 dark:text-red-400 bg-red-50 dark:bg-red-950/30 rounded-lg px-3 py-2">{error}</p>
                )}

                <button
                  onClick={handleVerifyOTP}
                  disabled={loading || otp.join("").length !== 6}
                  className="w-full flex items-center justify-center gap-2 py-3 rounded-xl bg-gradient-to-r from-brand-600 to-brand-700 text-white font-medium shadow-md shadow-brand-200 hover:shadow-lg hover:shadow-brand-300 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
                >
                  {loading ? (
                    <Loader2 className="h-5 w-5 animate-spin" />
                  ) : (
                    <>
                      Verify & Log In
                      <ShieldCheck className="h-4 w-4" />
                    </>
                  )}
                </button>

                <div className="flex items-center justify-between text-xs">
                  <button
                    onClick={() => {
                      setStep("phone");
                      setOtp(["", "", "", "", "", ""]);
                      setError("");
                    }}
                    className="text-surface-500 dark:text-gray-400 hover:text-surface-700 dark:hover:text-gray-300 transition-colors"
                  >
                    ← Change number
                  </button>
                  {countdown > 0 ? (
                    <span className="text-surface-400 dark:text-gray-500">
                      Resend in {Math.floor(countdown / 60)}:{String(countdown % 60).padStart(2, "0")}
                    </span>
                  ) : (
                    <button
                      onClick={handleSendOTP}
                      disabled={loading}
                      className="text-brand-600 dark:text-brand-400 hover:text-brand-700 dark:hover:text-brand-300 font-medium transition-colors"
                    >
                      Resend code
                    </button>
                  )}
                </div>
              </div>
            </>
          )}
        </div>

        {/* Footer hint */}
        <p className="text-center text-xs text-surface-400 dark:text-gray-500 mt-6">
          Your phone number is used to keep your memories private and separate from other users.
        </p>
      </div>
    </div>
  );
}
