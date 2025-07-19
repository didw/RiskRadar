import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "RiskRadar - 기업 리스크 모니터링 플랫폼",
  description: "실시간 기업 리스크 모니터링 및 분석 대시보드",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="ko" suppressHydrationWarning>
      <body className={inter.className}>{children}</body>
    </html>
  );
}