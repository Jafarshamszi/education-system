import { redirect } from "next/navigation"

/**
 * Catch-all redirect for requests
 * Redirects from /requests/[...path] to /dashboard/requests/[...path]
 */
export default function RequestsCatchAllRedirect({ params }: { params: { path: string[] } }) {
  const pathString = params.path.join("/")
  redirect(`/dashboard/requests/${pathString}`)
}