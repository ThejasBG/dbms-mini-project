"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { User } from "@/lib/types";

export default function SiteHeader() {
  const pathname = usePathname();
  const router = useRouter();
  const [user, setUser] = useState<User | null>(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    let alive = true;
    api<{ user: User | null }>("/api/auth/me")
      .then((data) => { if (alive) setUser(data.user); })
      .catch(() => { if (alive) setUser(null); });
    return () => { alive = false; };
  }, [pathname]);

  async function signOut() {
    setBusy(true);
    try {
      await api<{ ok: boolean }>("/api/auth/logout", { method: "POST" });
      setUser(null);
      router.push("/");
      router.refresh();
    } catch {
      // Keep the current view if the backend cannot clear the session cookie.
    } finally {
      setBusy(false);
    }
  }

  const linkClass = (href: string) => `nav-link ${pathname === href ? "active" : ""}`;
  return (
    <header className="site-header">
      <div className="header-inner">
        <Link href="/" className="brand" aria-label="Steamish home">
          <span className="brand-mark">S</span>
          <span>steamish<span className="brand-dot">.</span><small>GAME DISCOVERY</small></span>
        </Link>
        <nav className="main-nav" aria-label="Main navigation">
          <Link className={linkClass("/")} href="/">Discover</Link>
          <Link className={linkClass("/recommendations")} href="/recommendations">For you</Link>
          <Link className={linkClass("/library")} href="/library">Library</Link>
          <Link className={linkClass("/wishlist")} href="/wishlist">Wishlist</Link>
          <Link className={linkClass("/analytics")} href="/analytics">Insights</Link>
          {user?.role === "admin" && <Link className={linkClass("/admin")} href="/admin">Admin</Link>}
        </nav>
        <div className="header-account">
          {user ? (
            <>
              <span className="user-chip"><span className="online-dot" />{user.username}</span>
              <button className="button button-quiet button-small" onClick={signOut} disabled={busy}>{busy ? "Signing out…" : "Sign out"}</button>
            </>
          ) : (
            <>
              <Link className="button button-quiet button-small" href="/login">Sign in</Link>
              <Link className="button button-primary button-small" href="/register">Join free <span aria-hidden>↗</span></Link>
            </>
          )}
        </div>
      </div>
      <div className="mobile-nav">
        <Link href="/">Discover</Link><Link href="/recommendations">For you</Link><Link href="/library">Library</Link><Link href="/wishlist">Wishlist</Link><Link href="/analytics">Insights</Link>{user?.role === "admin" && <Link href="/admin">Admin</Link>}
      </div>
    </header>
  );
}
