import {
  Breadcrumb,
  BreadcrumbItem,
  BreadcrumbList,
  BreadcrumbSeparator,
} from "@/components/ui/breadcrumb";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { notFound } from "next/navigation";
import { Suspense } from "react";
import { SpoolConfiguration } from "./SpoolConfiguration";
import { Button } from "@/components/ui/button";
import Link from "next/link";
import { Skeleton } from "@/components/ui/skeleton";
import { getRfidTag } from "@/lib/printer";
import { getSpoolInTray, isLocked } from "@/lib/settings";
import { RfidLinkButton } from "./RfidLinkButton";
import { supportsTrayLocking } from "@/lib/features";

type Props = PageProps<"/ams/[amsId]/tray/[trayId]">;

function SkeletonPage() {
  return (
    <>
      <Breadcrumb>
        <BreadcrumbList>
          <BreadcrumbItem>Home</BreadcrumbItem>
          <BreadcrumbSeparator />
          <BreadcrumbItem>
            <Skeleton className="w-20 h-5" />
          </BreadcrumbItem>
          <BreadcrumbSeparator />
          <BreadcrumbItem>
            <Skeleton className="w-20 h-5" />
          </BreadcrumbItem>
        </BreadcrumbList>
      </Breadcrumb>
      <Card className="mt-6">
        <CardContent className="pt-6">
          <Skeleton className="w-full h-48" />
          <Button variant="outline" className="mt-4 float-left" asChild>
            <Link href="/">Back</Link>
          </Button>
        </CardContent>
      </Card>
    </>
  );
}

type RfidProps = {
  trayId: number;
};

async function RfidSettings({ trayId }: RfidProps) {
  const rfidTag = await getRfidTag(trayId);
  const locked = await isLocked(trayId);
  const spool = await getSpoolInTray(trayId);

  if (!rfidTag || locked || !spool) {
    return null;
  }

  return (
    <Card className="mt-6">
      <CardHeader>
        <CardTitle>RFID Tag</CardTitle>
      </CardHeader>
      <CardContent>
        <p className="text-foreground">
          A Spool with an RFID tag is is detected. If you want to automatically
          assign this spool to the tray when it&apos;s inserted, click the
          button below.
        </p>
        <div className="mt-2 block">
          RFID Tag: <pre className="font-mono inline">{rfidTag}</pre>
        </div>
        <RfidLinkButton spoolId={spool.id} uuid={rfidTag} />
      </CardContent>
    </Card>
  );
}

async function TrayPage(props: Props) {
  const params = await props.params;
  const amsId = Number(params.amsId) - 1;
  const rawTrayId = Number(params.trayId) - 1; // Convert to 0-indexed

  const trayId = amsId * 4 + rawTrayId;

  const minTray = amsId * 4;
  const maxTray = amsId * 4 + 4;

  if (trayId > maxTray || trayId < minTray) {
    notFound();
  }

  const trayLockingSupported = await supportsTrayLocking();

  return (
    <>
      <Breadcrumb>
        <BreadcrumbList>
          <BreadcrumbItem>Home</BreadcrumbItem>
          <BreadcrumbSeparator />
          <BreadcrumbItem>AMS {amsId + 1}</BreadcrumbItem>
          <BreadcrumbSeparator />
          <BreadcrumbItem>Tray {(rawTrayId % 4) + 1}</BreadcrumbItem>
        </BreadcrumbList>
      </Breadcrumb>
      {trayLockingSupported && <RfidSettings trayId={trayId} />}
      <Card className="mt-6">
        <CardContent className="pt-6">
          <SpoolConfiguration trayId={trayId} />
          <Button variant="outline" className="mt-4 float-left" asChild>
            <Link href="/">Back</Link>
          </Button>
        </CardContent>
      </Card>
    </>
  );
}

export default async function TrayPageOuter(props: Props) {
  return (
    <div className="container mx-auto p-4 max-w-2xl">
      <Suspense fallback={<SkeletonPage />}>
        <TrayPage {...props} />
      </Suspense>
    </div>
  );
}
