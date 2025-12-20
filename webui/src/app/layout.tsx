import type { Metadata } from "next";
import "./globals.css";
import { Inter } from "next/font/google";
import React from "react";
import { NuqsAdapter } from "nuqs/adapters/next/app";
import Link from "next/link";

const inter = Inter({
  subsets: ["latin"],
  preload: true,
  display: "swap",
});

export const metadata: Metadata = {
  title: "AI Skill Agent",
  description: "AI Agent for Game Skill Management with RAG",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className={`${inter.className} flex flex-col h-screen overflow-hidden`}>
        <nav className="border-b bg-white flex-shrink-0">
          <div className="container mx-auto px-4 py-2">
            <div className="flex items-center gap-6">
              <Link href="/" className="text-lg font-bold text-gray-800 hover:text-blue-600">
                Skill Agent
              </Link>
              <div className="flex gap-4">
                <Link href="/" className="text-gray-600 hover:text-gray-800 hover:underline">
                  对话
                </Link>
                <Link href="/rag" className="text-gray-600 hover:text-gray-800 hover:underline">
                  RAG功能
                </Link>
              </div>
            </div>
          </div>
        </nav>
        <main className="flex-1 overflow-hidden">
          <NuqsAdapter>{children}</NuqsAdapter>
        </main>
      </body>
    </html>
  );
}
