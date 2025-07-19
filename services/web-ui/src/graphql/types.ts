export interface DateRangeInput {
  from: string;
  to: string;
}

export interface CompanyRiskFilter {
  industries?: string[];
  riskLevels?: string[];
  searchTerm?: string;
  dateRange?: DateRangeInput;
}

export interface CompanyRiskSort {
  field: 'name' | 'riskScore' | 'change' | 'lastUpdated';
  order: 'asc' | 'desc';
}

export interface PaginationInput {
  page: number;
  limit: number;
}

export interface CompanyFilter {
  industries?: string[];
  riskLevels?: string[];
}

export interface CompanySort {
  field: 'name' | 'riskScore' | 'marketCap';
  order: 'asc' | 'desc';
}

export interface AlertSettingsInput {
  enabled: boolean;
  thresholds: {
    riskScore?: number;
    changePercent?: number;
  };
  channels: {
    email?: boolean;
    sms?: boolean;
    push?: boolean;
  };
}

export type ReportType = 'summary' | 'detailed' | 'executive';
export type ExportFormat = 'csv' | 'excel' | 'pdf';

export interface RiskDataFilter {
  companyIds?: string[];
  dateRange?: DateRangeInput;
  industries?: string[];
}