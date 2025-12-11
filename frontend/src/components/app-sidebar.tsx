"use client"

import * as React from "react"
import {
  IconDashboard,
  IconInnerShadowTop,
  IconSearch,
  IconSettings,
  IconUsers,
  IconCalendar,
  IconFileText,
  IconBuilding,
  IconCalculator,
  IconClipboardList,
  IconSchool,
  IconBook,
  IconBooks,
  IconClock,
} from "@tabler/icons-react"

import { NavMain } from "@/components/nav-main"
import { NavSecondary } from "@/components/nav-secondary"
import { NavUser } from "@/components/nav-user"
import { useLanguage } from "@/contexts/LanguageContext"
import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarHeader,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
} from "@/components/ui/sidebar"

export function AppSidebar({ ...props }: React.ComponentProps<typeof Sidebar>) {
  const { t } = useLanguage();

  const data = {
    navMain: [
      {
        title: t("sidebar.dashboard"),
        url: "/dashboard",
        icon: IconDashboard,
      },
    ],
    // Academic Management
    navAcademic: [
      {
        title: t("sidebar.students"),
        url: "/dashboard/students",
        icon: IconUsers,
      },
      {
        title: t("sidebar.teachers"),
        url: "/dashboard/teachers",
        icon: IconSchool,
      },
      {
        title: t("sidebar.studentGroups"),
        url: "/dashboard/student-groups",
        icon: IconUsers,
      },
      {
        title: t("sidebar.evaluationSystem"),
        url: "/dashboard/evaluation-system",
        icon: IconCalculator,
      },
    ],
    // Curriculum & Planning
    navCurriculum: [
      {
        title: t("sidebar.educationPlans"),
        url: "/dashboard/education-plans",
        icon: IconBook,
      },
      {
        title: t("sidebar.curriculum"),
        url: "/dashboard/curriculum",
        icon: IconBooks,
      },
      {
        title: t("sidebar.academicSchedule"),
        url: "/dashboard/academic-schedule",
        icon: IconCalendar,
      },
      {
        title: t("sidebar.classSchedule"),
        url: "/dashboard/class-schedule",
        icon: IconClock,
      },
    ],
    // Administration
    navAdministration: [
      {
        title: t("sidebar.requests"),
        url: "/dashboard/requests",
        icon: IconFileText,
      },
      {
        title: t("sidebar.studentOrders"),
        url: "/dashboard/student-orders",
        icon: IconClipboardList,
      },
      {
        title: t("sidebar.organization"),
        url: "/dashboard/organizations",
        icon: IconBuilding,
      },
    ],
    navSecondary: [
      {
        title: t("sidebar.settings"),
        url: "/dashboard/settings",
        icon: IconSettings,
      },
      {
        title: t("sidebar.search"),
        url: "#",
        icon: IconSearch,
      },
    ],
  };


  return (
    <Sidebar collapsible="offcanvas" {...props}>
      <SidebarHeader>
        <SidebarMenu>
          <SidebarMenuItem>
            <SidebarMenuButton
              asChild
              className="data-[slot=sidebar-menu-button]:!p-1.5"
            >
              <a href="#">
                <IconInnerShadowTop className="!size-5" />
                <span className="text-base font-semibold">Acme Inc.</span>
              </a>
            </SidebarMenuButton>
          </SidebarMenuItem>
        </SidebarMenu>
      </SidebarHeader>
      <SidebarContent>
        <NavMain items={data.navMain} />

        {/* Academic Management Section */}
        <div className="px-3 py-2">
          <h4 className="mb-2 text-xs font-semibold text-muted-foreground uppercase tracking-wider">
            {t("sidebar.academicManagement")}
          </h4>
          <SidebarMenu>
            {data.navAcademic.map((item) => (
              <SidebarMenuItem key={item.title}>
                <SidebarMenuButton tooltip={item.title} asChild>
                  <a href={item.url}>
                    {item.icon && <item.icon />}
                    <span>{item.title}</span>
                  </a>
                </SidebarMenuButton>
              </SidebarMenuItem>
            ))}
          </SidebarMenu>
        </div>

        {/* Curriculum & Planning Section */}
        <div className="px-3 py-2">
          <h4 className="mb-2 text-xs font-semibold text-muted-foreground uppercase tracking-wider">
            {t("sidebar.curriculumPlanning")}
          </h4>
          <SidebarMenu>
            {data.navCurriculum.map((item) => (
              <SidebarMenuItem key={item.title}>
                <SidebarMenuButton tooltip={item.title} asChild>
                  <a href={item.url}>
                    {item.icon && <item.icon />}
                    <span>{item.title}</span>
                  </a>
                </SidebarMenuButton>
              </SidebarMenuItem>
            ))}
          </SidebarMenu>
        </div>

        {/* Administration Section */}
        <div className="px-3 py-2">
          <h4 className="mb-2 text-xs font-semibold text-muted-foreground uppercase tracking-wider">
            {t("sidebar.administration")}
          </h4>
          <SidebarMenu>
            {data.navAdministration.map((item) => (
              <SidebarMenuItem key={item.title}>
                <SidebarMenuButton tooltip={item.title} asChild>
                  <a href={item.url}>
                    {item.icon && <item.icon />}
                    <span>{item.title}</span>
                  </a>
                </SidebarMenuButton>
              </SidebarMenuItem>
            ))}
          </SidebarMenu>
        </div>

        <NavSecondary items={data.navSecondary} className="mt-auto" />
      </SidebarContent>
      <SidebarFooter>
        <NavUser />
      </SidebarFooter>
    </Sidebar>
  )
}
