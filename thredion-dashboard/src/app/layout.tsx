import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Thredion — AI Cognitive Memory Engine",
  description:
    "Transform social media saves into an intelligent, searchable, self-organizing knowledge system. Your AI Second Brain.",
  icons: { icon: "/favicon.ico" },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-surface-50">{children}</body>
    </html>
  );
}
