export const apiUrl = process.env.API_INTERNAL_URL ?? process.env.NEXT_PUBLIC_API_URL ?? "http://api:8000";

export async function apiGet<T>(path:string, fallback:T):Promise<T>{
  try { const response=await fetch(`${apiUrl}${path}`,{cache:"no-store"}); return response.ok?response.json():fallback; }
  catch { return fallback; }
}
