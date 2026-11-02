export async function login(email: string, password: string) {
  const r = await fetch("/api/login", { method: "POST", body: JSON.stringify({ email, password }) });
  return r.json(); // { token: string, expiresIn: 3600 }
}
