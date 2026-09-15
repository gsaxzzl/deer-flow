"use client";

import { PlugIcon } from "lucide-react";

import { CONNECTORS } from "@/core/connectors";
import { useI18n } from "@/core/i18n/hooks";

export function ConnectorGallery() {
  const { t } = useI18n();

  return (
    <div className="flex size-full flex-col">
      {/* Page header */}
      <div className="flex items-center justify-between border-b px-6 py-4">
        <div>
          <h1 className="text-xl font-semibold">{t.connectors.title}</h1>
          <p className="text-muted-foreground mt-0.5 text-sm">
            {t.connectors.description}
          </p>
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-6">
        {CONNECTORS.length === 0 ? (
          <div className="flex h-64 flex-col items-center justify-center gap-3 text-center">
            <div className="bg-muted flex h-14 w-14 items-center justify-center rounded-full">
              <PlugIcon className="text-muted-foreground h-7 w-7" />
            </div>
            <div>
              <p className="font-medium">{t.connectors.emptyTitle}</p>
              <p className="text-muted-foreground mt-1 text-sm">
                {t.connectors.emptyDescription}
              </p>
            </div>
          </div>
        ) : (
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {CONNECTORS.map((connector) => {
              const Card = connector.Card;
              return <Card key={connector.id} />;
            })}
          </div>
        )}
      </div>
    </div>
  );
}
