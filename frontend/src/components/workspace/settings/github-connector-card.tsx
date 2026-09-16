"use client";

import { CheckCircle2Icon, GithubIcon, LoaderCircleIcon, PlugIcon } from "lucide-react";
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
import { useConnectorAuth, useSaveConnectorAuth } from "@/core/connectors";
import { cn } from "@/lib/utils";

interface GithubFormValues {
  repo_url: string;
  authorization: string;
}

const EMPTY_FORM: GithubFormValues = {
  repo_url: "",
  authorization: "",
};

export function GithubConnectorCard() {
  const { data, isLoading } = useConnectorAuth("github");
  const saveMutation = useSaveConnectorAuth();
  const [dialogOpen, setDialogOpen] = useState(false);
  const [form, setForm] = useState<GithubFormValues>(EMPTY_FORM);

  const configured = !!data && data.status === "active";

  useEffect(() => {
    if (data) {
      const meta = data.metadata ?? {};
      setForm({
        repo_url: meta.repo_url ?? "",
        authorization: data.authorization ?? "",
      });
    }
  }, [data]);

  const handleSave = () => {
    if (!form.repo_url || !form.authorization) {
      toast.error("请填写 GitHub 仓库地址和 Fine-grained Token");
      return;
    }
    saveMutation.mutate(
      {
        connector_type: "github",
        authorization: form.authorization,
        metadata: {
          repo_url: form.repo_url,
        },
      },
      {
        onSuccess: () => {
          toast.success("GitHub 连接器凭证已保存");
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
          <GithubIcon className="size-5" />
        </ItemMedia>
        <ItemContent className="min-w-0">
          <ItemTitle className="w-full">
            <span className="truncate">GitHub 连接器</span>
            <Badge
              variant={configured ? "default" : "outline"}
              className={cn(!configured && "text-muted-foreground")}
            >
              {configured ? <CheckCircle2Icon /> : <PlugIcon />}
              {configured ? "已配置" : "未配置"}
            </Badge>
          </ItemTitle>
          <ItemDescription className="line-clamp-none">
            查询 GitHub 仓库信息、提交历史和 Issue 列表。在聊天中输入「看看 xxx
            仓库最近的提交」即可自动调用。
            {configured && data?.metadata?.repo_url
              ? ` 当前仓库: ${data.metadata.repo_url}`
              : " 请先配置仓库地址和 Fine-grained Token。"}
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
            <DialogTitle>GitHub 连接器配置</DialogTitle>
            <DialogDescription>
              填写 GitHub 仓库地址和 Fine-grained Token，保存后即可在聊天中查询仓库信息、提交历史和
              Issue。
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-2">
            <div className="space-y-1.5">
              <label className="text-sm font-medium">GitHub 仓库地址</label>
              <Input
                type="text"
                placeholder="https://github.com/gsaxzzl/deer-flow"
                value={form.repo_url}
                onChange={(e) =>
                  setForm((f) => ({ ...f, repo_url: e.target.value }))
                }
              />
              <p className="text-muted-foreground text-xs">
                作为默认仓库，聊天中未指定仓库时自动使用；也可同时配置多个连接器指向不同仓库。
              </p>
            </div>
            <div className="space-y-1.5">
              <label className="text-sm font-medium">Fine-grained Token</label>
              <Input
                type="password"
                placeholder="github_pat_..."
                value={form.authorization}
                onChange={(e) =>
                  setForm((f) => ({ ...f, authorization: e.target.value }))
                }
              />
              <p className="text-muted-foreground text-xs">
                在 GitHub → Settings → Developer settings → Fine-grained tokens
                中生成，需勾选 Metadata: Read、Contents: Read、Issues: Read
                权限。Token 仅保存在本地，不会上传。
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
