import type { Metadata } from "next";
import SiteHeader from "@/components/SiteHeader";
import "./globals.css";

export const metadata: Metadata = {
  title: "Steamish — Find your next favourite game",
  description: "Discover games by genre, platform, ratings, and vector-powered recommendations.",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body>
        <SiteHeader />
        <main className="page-shell">{children}</main>
        <footer className="site-footer">
          <div className="footer-inner"><span className="footer-brand">steamish<span className="brand-dot">.</span></span><span>Find the games that feel made for you.</span><span className="footer-note">Academic project · Game metadata only</span></div>
        </footer>
      </body>
    </html>
  );
}
