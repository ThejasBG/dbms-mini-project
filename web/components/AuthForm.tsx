"use client";

import Link from "next/link";
import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";
import { api, ApiError, jsonBody } from "@/lib/api";
import type { User } from "@/lib/types";

export default function AuthForm({ mode }: { mode: "login" | "register" }) {
  const router = useRouter();
  const registering = mode === "register";
  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); setBusy(true); setError("");
    try {
      const endpoint = registering ? "/api/auth/register" : "/api/auth/login";
      const payload = registering ? { username: username.trim(), email: email.trim(), password } : { email: email.trim(), password };
      await api<{ user: User }>(endpoint, { method: "POST", body: jsonBody(payload) });
      router.push("/"); router.refresh();
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Could not complete the request.");
    } finally { setBusy(false); }
  }

  return (
    <div className="auth-wrap">
      <div className="auth-card">
        <div className="eyebrow">{registering ? "Your next chapter starts here" : "Welcome back, player"}</div>
        <h1>{registering ? "Create your account." : "Good to see you."}</h1>
        <p>{registering ? "Save your discoveries, curate your wishlist, and get game recommendations tuned to your interests." : "Sign in to get back to your wishlist, library, reviews, and tailored discoveries."}</p>
        <form onSubmit={submit}>
          {registering && <div className="form-field"><label className="form-label" htmlFor="username">Username</label><input id="username" className="form-input" value={username} onChange={(e) => setUsername(e.target.value)} required minLength={3} maxLength={32} pattern="[A-Za-z0-9_-]+" autoComplete="username" placeholder="PlayerOne" /><div className="form-help">3–32 letters, numbers, underscores, or hyphens.</div></div>}
          <div className="form-field"><label className="form-label" htmlFor="email">Email address</label><input id="email" className="form-input" type="email" value={email} onChange={(e) => setEmail(e.target.value)} required maxLength={254} autoComplete="email" placeholder="you@example.com" /></div>
          <div className="form-field"><label className="form-label" htmlFor="password">Password</label><input id="password" className="form-input" type="password" value={password} onChange={(e) => setPassword(e.target.value)} required minLength={registering ? 10 : 1} maxLength={128} autoComplete={registering ? "new-password" : "current-password"} placeholder={registering ? "At least 10 characters" : "Your password"} />{registering && <div className="form-help">Use at least 10 characters. Passwords are stored as salted hashes.</div>}</div>
          {error && <div className="error-text" role="alert" style={{ margin: "5px 0 15px" }}>{error}</div>}
          <button type="submit" className="button button-primary button-block" disabled={busy}>{busy ? "Please wait…" : registering ? "Create account" : "Sign in"}</button>
        </form>
        <div className="auth-switch">{registering ? <>Already have an account? <Link href="/login">Sign in</Link></> : <>New to Steamish? <Link href="/register">Create an account</Link></>}</div>
      </div>
      <p className="form-help" style={{ textAlign: "center", marginTop: 14 }}>Academic project. Use a password you do not reuse for important accounts.</p>
    </div>
  );
}
