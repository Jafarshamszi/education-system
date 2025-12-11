"use client"

import React, { useEffect, useState } from "react"
import { SidebarProvider, SidebarTrigger } from "@/components/ui/sidebar"
import { AppSidebar } from "@/components/app-sidebar"
import { Separator } from "@/components/ui/separator"

export default function AuthenticatedLayout({
  children,
}: {
  children: React.ReactNode
}) {
  // Detect whether an ancestor layout has already rendered the sidebar.
  // Some pages (like those under /dashboard) are wrapped by a parent
  // layout that already provides SidebarProvider + AppSidebar. Rendering
  // a second provider causes duplicate sidebars and the visual bug
  // where closing one leaves the other visible. We check the DOM for
  // the sidebar wrapper element and avoid rendering a second one.
  const [hasParentSidebar, setHasParentSidebar] = useState<boolean | null>(null)

  useEffect(() => {
    const exists = !!document.querySelector('[data-slot="sidebar-wrapper"]')
    setHasParentSidebar(exists)
  }, [])

  // While we haven't determined whether a parent sidebar exists, render
  // a minimal skeleton to avoid errors from SidebarTrigger (which requires
  // a provider). We keep this minimal to avoid flashing a duplicate sidebar
  // before the check completes.
  if (hasParentSidebar === null) {
    return <div className="flex-1">{children}</div>
  }

  // If a parent provided the sidebar, do not render another SidebarProvider
  // or AppSidebar here. Just render the main content and the trigger which
  // will use the upstream provider.
  if (hasParentSidebar) {
    return (
      <main className="flex-1 flex flex-col">
        <header className="flex h-16 shrink-0 items-center gap-2 px-4">
          <SidebarTrigger className="-ml-1" />
          <Separator orientation="vertical" className="mr-2 h-4" />
          <div className="flex-1" />
        </header>
        <div className="flex-1 overflow-auto">
          {children}
        </div>
      </main>
    )
  }

  // Otherwise render a local SidebarProvider and AppSidebar for pages that
  // don't have an upstream provider.
  return (
    <SidebarProvider>
      <AppSidebar />
      <main className="flex-1 flex flex-col">
        <header className="flex h-16 shrink-0 items-center gap-2 px-4">
          <SidebarTrigger className="-ml-1" />
          <Separator orientation="vertical" className="mr-2 h-4" />
          <div className="flex-1" />
        </header>
        <div className="flex-1 overflow-auto">
          {children}
        </div>
      </main>
    </SidebarProvider>
  )
}