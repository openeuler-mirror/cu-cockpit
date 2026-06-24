export interface PageQuery {
  page: number;
  limit: number;
}

export interface APIResponseData {
  code?: number;
  data: any;
  msg?: string;
}

export interface CurrentInfoType {
  role: string;
  model: string;
  app: string;

  menu: string;
}

export interface ModelItemType {
  app: string;
  key: string;
  title: string;
  showText?: string;
}
