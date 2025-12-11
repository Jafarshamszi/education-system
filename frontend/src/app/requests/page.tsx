import { redirect } from "next/navigation"

/**
 * Root redirect for requests
 * Redirects from /requests to /dashboard/requests
 */
export default function RequestsRedirect() {
  redirect("/dashboard/requests")
}