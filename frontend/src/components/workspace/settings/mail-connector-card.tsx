"use client";

import {
  CheckCircle2Icon,
  LoaderCircleIcon,
  MailIcon,
  PlugIcon,
} from "lucide-react";
import { useEffect, useState } from "react";
import { toast } from "sonner";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import {
  Item,
  ItemActions,
  ItemContent,
  ItemDescription,
  ItemMedia,
  ItemTitle,
} from "@/components/ui/item";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { useConnectorAuth, useSaveConnectorAuth } from "@/core/connectors";
import { cn } from "@/lib/utils";

interface MailFormValues {
  email: string;
  smtp_host: string;
  smtp_port: string;
  smtp_user: string;
  smtp_security: string;
  authorization: string;
}

const EMPTY_FORM: MailFormValues = {
  email: "",
  smtp_host: "",
  smtp_port: "465",
  smtp_user: "",
  smtp_security: "ssl",
  authorization: "",
};

export function MailConnectorCard() {
  const { data, isLoading } = useConnectorAuth("mail");
  const saveMutation = useSaveConnectorAuth();
  const [dialogOpen, setDialogOpen] = useState(false);
  const [form, setForm] = useState<MailFormValues>(EMPTY_FORM);

  const configured = !!data && data.status === "active";

  useEffect(() => {
    if (data) {
      const meta = data.metadata ?? {};
      setForm({
        email: meta.email ?? "",
        smtp_host: meta.smtp_host ?? "",
        smtp_port: String(meta.smtp_port ?? "465"),
        smtp_user: meta.smtp_user ?? meta.email ?? "",
        smtp_security: meta.smtp_security ?? "ssl",
        authorization: data.authorization ?? "",
      });
    }
  }, [data]);

  const handleSave = () => {
    if (!form.email || !form.smtp_host || !form.authorization) {
      toast.error("请填写邮箱地址、SMTP 服务器和授权码");
      return;
    }
    saveMutation.mutate(
      {
        connector_type: "mail",
        authorization: form.authorization,
        metadata: {
          email: form.email,
          smtp_host: form.smtp_host,
          smtp_port: Number(form.smtp_port) || 465,
          smtp_user: form.smtp_user || form.email,
          smtp_security: form.smtp_security,
        },
      },
      {
        onSuccess: () => {
          toast.success("邮件连接器凭证已保存");
          setDialogOpen(false);
        },
        onError: (e: unknown) => {
          toast.error(e instanceof Error ? e.message : "保存失败");
        },
      },
    );
  };

  return (
    <>
      <Item variant="outline" className="w-full items-start">
        <ItemMedia variant="icon" className="bg-background">
          <MailIcon className="size-5" />
        </ItemMedia>
        <ItemContent className="min-w-0">
          <ItemTitle className="w-full">
            <span className="truncate">邮件连接器</span>
            <Badge
              variant={configured ? "default" : "outline"}
              className={cn(!configured && "text-muted-foreground")}
            >
              {configured ? <CheckCircle2Icon /> : <PlugIcon />}
              {configured ? "已配置" : "未配置"}
            </Badge>
          </ItemTitle>
          <ItemDescription className="line-clamp-none">
            通过 SMTP 发送邮件。在聊天中输入「发邮件给 xxx」即可自动调用。
            {configured && data?.metadata?.email
              ? ` 当前邮箱: ${data.metadata.email}`
              : " 请先配置邮箱和 SMTP 授权凭证。"}
          </ItemDescription>
        </ItemContent>
        <ItemActions className="ml-auto">
          <Button
            type="button"
            variant="outline"
            size="sm"
            disabled={isLoading}
            onClick={() => setDialogOpen(true)}
          >
            {isLoading ? (
              <LoaderCircleIcon className="animate-spin" />
            ) : (
              <PlugIcon />
            )}
            {configured ? "修改" : "配置"}
          </Button>
        </ItemActions>
      </Item>

      <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle>邮件连接器配置</DialogTitle>
            <DialogDescription>
              填写邮箱地址和 SMTP 授权凭证，保存后即可在聊天中发送邮件。
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-2">
            <div className="space-y-1.5">
              <label className="text-sm font-medium">邮箱地址</label>
              <Input
                type="email"
                placeholder="you@example.com"
                value={form.email}
                onChange={(e) =>
                  setForm((f) => ({ ...f, email: e.target.value }))
                }
              />
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-1.5">
                <label className="text-sm font-medium">SMTP 服务器</label>
                <Input
                  placeholder="smtp.126.com"
                  value={form.smtp_host}
                  onChange={(e) =>
                    setForm((f) => ({ ...f, smtp_host: e.target.value }))
                  }
                />
              </div>
              <div className="space-y-1.5">
                <label className="text-sm font-medium">端口</label>
                <Input
                  type="number"
                  placeholder="465"
                  value={form.smtp_port}
                  onChange={(e) =>
                    setForm((f) => ({ ...f, smtp_port: e.target.value }))
                  }
                />
              </div>
            </div>
            <div className="space-y-1.5">
              <label className="text-sm font-medium">SMTP 用户名</label>
              <Input
                placeholder="默认同邮箱地址"
                value={form.smtp_user}
                onChange={(e) =>
                  setForm((f) => ({ ...f, smtp_user: e.target.value }))
                }
              />
            </div>
            <div className="space-y-1.5">
              <label className="text-sm font-medium">加密方式</label>
              <Select
                value={form.smtp_security}
                onValueChange={(v) =>
                  setForm((f) => ({ ...f, smtp_security: v }))
                }
              >
                <SelectTrigger className="w-full">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="ssl">SSL/TLS (端口 465)</SelectItem>
                  <SelectItem value="starttls">STARTTLS (端口 587)</SelectItem>
                  <SelectItem value="none">无加密 (端口 25)</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-1.5">
              <label className="text-sm font-medium">邮箱授权码</label>
              <Input
                type="password"
                placeholder="SMTP 授权码 / 密码"
                value={form.authorization}
                onChange={(e) =>
                  setForm((f) => ({ ...f, authorization: e.target.value }))
                }
              />
              <p className="text-muted-foreground text-xs">
                邮箱授权码不是登录密码，需在邮箱服务商设置中开启 SMTP
                并获取授权码。
              </p>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setDialogOpen(false)}>
              取消
            </Button>
            <Button onClick={handleSave} disabled={saveMutation.isPending}>
              {saveMutation.isPending && (
                <LoaderCircleIcon className="animate-spin" />
              )}
              保存
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  );
}
