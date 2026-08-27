import { Card, CardContent } from "@/components/ui/card";
import { SpoolConfiguration } from "../ams/[amsId]/tray/[trayId]/SpoolConfiguration";
import { Button } from "@/components/ui/button";
import Link from "next/link";
import { Suspense } from "react";
import { Skeleton } from "@/components/ui/skeleton";
import { headers } from "next/headers";

function SkeletonPage() {
  return (
    <Card className="mt-6">
      <CardContent className="pt-6">
        <Skeleton className="w-full h-48" />
        <Button variant="outline" className="mt-4 float-left" asChild>
          <Link href="/">Back</Link>
        </Button>
      </CardContent>
    </Card>
  );
}

async function ExternalSpoolConfiguration() {
  // Force the page to be dynamic
  await headers();
  return (
    <Card className="mt-6">
      <CardContent className="pt-6">
        <SpoolConfiguration trayId={255} />
        <Button variant="outline" className="mt-4 float-left" asChild>
          <Link href="/">Back</Link>
        </Button>
      </CardContent>
    </Card>
  );
}

export default async function ExternalSpoolPage() {
  return (
    <div className="container mx-auto p-4 max-w-2xl">
      <Suspense fallback={<SkeletonPage />}>
        <ExternalSpoolConfiguration />
      </Suspense>
    </div>
  );
}
