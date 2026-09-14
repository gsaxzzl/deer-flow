/** 连接器凭证类型。 */

export interface ConnectorAuth {
  username: string;
  connector_type: string;
  authorization: string;
  metadata: ConnectorMetadata;
  status: string;
}

export interface ConnectorMetadata {
  email?: string;
  smtp_host?: string;
  smtp_port?: number;
  smtp_user?: string;
  smtp_security?: string;
  [key: string]: unknown;
}

export interface SaveConnectorAuthRequest {
  connector_type: string;
  authorization: string;
  metadata: ConnectorMetadata;
}
