export interface PageQuery {
  page: number;
  limit: number;
}

export interface APIResponseData {
  code?: number;
  data: any;
  msg?: string;
}
