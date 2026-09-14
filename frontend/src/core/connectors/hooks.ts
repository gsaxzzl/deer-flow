import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { getConnectorAuth, saveConnectorAuth } from "./api";
import type { SaveConnectorAuthRequest } from "./types";

export function useConnectorAuth(connectorType: string) {
  return useQuery({
    queryKey: ["connectorAuth", connectorType],
    queryFn: () => getConnectorAuth(connectorType),
    retry: false,
  });
}

export function useSaveConnectorAuth() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (body: SaveConnectorAuthRequest) => saveConnectorAuth(body),
    onSuccess: (_data, variables) => {
      void queryClient.invalidateQueries({
        queryKey: ["connectorAuth", variables.connector_type],
      });
    },
  });
}
