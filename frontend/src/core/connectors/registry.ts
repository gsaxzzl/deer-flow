"use client";

import { MailIcon } from "lucide-react";

import { MailConnectorCard } from "@/components/workspace/settings/mail-connector-card";

/**
 * 连接器定义。
 *
 * 新增连接器（如知识库连接器）时，只需创建对应的卡片组件并在此数组中追加一项，
 * 连接器列表页会自动展示，无需改动列表页本身。
 */
export interface ConnectorDefinition {
  /** 连接器唯一标识，与后端 connector_type 对应 */
  id: string;
  /** 显示名称 */
  label: string;
  /** 卡片描述 */
  description: string;
  /** 图标组件（lucide-react） */
  icon: React.ComponentType<{ className?: string }>;
  /** 该连接器的卡片组件（负责展示状态与配置弹窗） */
  Card: React.ComponentType;
}

export const CONNECTORS: ConnectorDefinition[] = [
  {
    id: "mail",
    label: "邮件连接器",
    description: "通过 SMTP 发送邮件。在聊天中输入「发邮件给 xxx」即可自动调用。",
    icon: MailIcon,
    Card: MailConnectorCard,
  },
];
