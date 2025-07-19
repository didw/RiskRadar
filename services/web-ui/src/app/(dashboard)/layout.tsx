import { DashboardNav } from "@/components/layout/dashboard-nav";
import { DashboardHeader } from "@/components/layout/dashboard-header";

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="flex h-screen overflow-hidden">
      <DashboardNav />
      <div className="flex-1 flex flex-col overflow-hidden">
        <DashboardHeader />
        <main className="flex-1 overflow-y-auto bg-gray-50 dark:bg-gray-900">
          <div className="container mx-auto p-6">
            {children}
          </div>
        </main>
      </div>
    </div>
  );
}