import AmsComponent from "@/components/AmsComponent";
import {
  Breadcrumb,
  BreadcrumbItem,
  BreadcrumbList,
} from "@/components/ui/breadcrumb";
import { Suspense } from "react";
import { Skeleton } from "@/components/ui/skeleton";
import { getSettings } from "@/lib/settings";
import { Button } from "@/components/ui/button";
import Link from "next/link";
import { headers } from "next/headers";

function SkeletonPage() {
  return (
    <>
      <Breadcrumb>
        <BreadcrumbList>
          <BreadcrumbItem>Home</BreadcrumbItem>
        </BreadcrumbList>
      </Breadcrumb>
      <div className="mt-6">
        <h1 className="text-2xl font-semibold mb-4">
          BambuLab Spoolman Integration
        </h1>
      </div>
    </>
  );
}

async function AmsConfiguration() {
  const settings = await getSettings();
  const trayCount = settings.trayCount;
  const amsCount = Math.ceil(trayCount / 4);
  const components = [];
  for (let i = 0; i < amsCount; i++) {
    components.push(<AmsComponent key={i} id={i} />);
  }
  return components;
}

async function HomePage() {
  // Force the page to be dynamic
  await headers();
  return (
    <>
      <Breadcrumb>
        <BreadcrumbList>
          <BreadcrumbItem>Home</BreadcrumbItem>
        </BreadcrumbList>
      </Breadcrumb>
      <div className="mt-6">
        <h1 className="text-2xl font-semibold mb-4">
          BambuLab Spoolman Integration
        </h1>
        <div className="mb-6">
          <Link href="/external-spool">
            <Button variant="outline">Configure External Spool</Button>
          </Link>
        </div>
        <div className="flex flex-col gap-4">
          <AmsConfiguration />
        </div>
      </div>
    </>
  );
}

export default async function Home() {
  return (
    <div className="container mx-auto p-4 max-w-2xl">
      <Suspense fallback={<SkeletonPage />}>
        <HomePage />
      </Suspense>
    </div>
  );
}
