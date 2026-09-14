import { fetch } from "@/core/api/fetcher";
import { getBackendBaseURL } from "@/core/config";

import type { ConnectorAuth, SaveConnectorAuthRequest } from "./types";

async function readErrorDetail(
  response: Response,
  fallback: string,
): Promise<string> {
  const error = (await response.json().catch(() => ({}))) as {
    detail?: unknown;
  };
  return typeof error.detail === "string" ? error.detail : fallback;
}

export async function saveConnectorAuth(
  body: SaveConnectorAuthRequest,
): Promise<ConnectorAuth> {
  const response = await fetch(`${getBackendBaseURL()}/api/connectors/auth`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!response.ok) {
    throw new Error(await readErrorDetail(response, "保存连接器凭证失败"));
  }
  return response.json() as Promise<ConnectorAuth>;
}

export async function getConnectorAuth(
  connectorType: string,
): Promise<ConnectorAuth> {
  const response = await fetch(
    `${getBackendBaseURL()}/api/connectors/auth/${connectorType}`,
  );
  if (!response.ok) {
    throw new Error(await readErrorDetail(response, "获取连接器凭证失败"));
  }
  return response.json() as Promise<ConnectorAuth>;
}
