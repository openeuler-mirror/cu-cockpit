export interface TreeType {
  id: number;
  name: string;
  status: boolean;
  children?: TreeType[];
}

export interface APIResponseData {
  code?: number;
  data: [];
  msg?: string;
}