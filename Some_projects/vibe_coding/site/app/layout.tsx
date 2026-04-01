import type { Metadata } from "next";
import { Inter, Space_Grotesk } from "next/font/google";

import "./globals.css";
import { cn } from "@/lib/cn";

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-inter",
});

const spaceGrotesk = Space_Grotesk({
  subsets: ["latin"],
  variable: "--font-display",
});

export const metadata: Metadata = {
  title: "Muhammad Usman Noor | Robotics & AI",
  description:
    "Computer Vision • Machine Learning • ROS2 — building full‑stack robotics systems that bridge perception, navigation, and real-world deployment.",
};

import { Chat } from "@/components/ui/chat";
export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="en"
      className={cn(inter.variable, spaceGrotesk.variable, "font-sans")}
    >
      <body className="min-h-screen antialiased text-fg">
        {children}
        <Chat />
      </body>
    </html>
  );
}

