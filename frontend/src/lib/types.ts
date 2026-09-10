export type ProjectStatus = 'draft' | 'in_progress' | 'processing' | 'under_review' | 'completed' | 'failed';
export type FileStatus = 'uploaded' | 'processing' | 'parsed' | 'failed';
export type AuditStatus = 'CLEARED' | 'FLAGGED' | 'REJECTED' | 'REVIEW REQUIRED' | 'PENDING';

export interface Client {
  id: string;
  name: string;
  industry?: string;
  fiscal_year_end?: string;
  contact_email?: string;
  created_at: string;
  updated_at: string;
}

export interface Project {
  id: string;
  client_id: string;
  title: string;
  audit_year: number;
  status: ProjectStatus;
  description?: string;
  created_at: string;
  updated_at: string;
}

export interface FileRecord {
  id: string;
  project_id: string;
  filename: string;
  file_type: 'xlsx' | 'xls' | 'pdf';
  file_size_bytes: number;
  status: FileStatus;
  download_url?: string;
  created_at: string;
  updated_at: string;
}

export interface VerificationProcedure {
  procedure_id: string;
  procedure_name: string;
  statement_type?: string;
  status: 'PASS' | 'FLAGGED' | 'FAIL' | 'REJECTED';
  detail: string;
  variance?: number;
  benchmark?: string;
}

export interface VerificationData {
  overall_status: AuditStatus;
  conclusion?: string | {
    text?: string;
    overall_status?: string;
    procedures_passed?: number;
    total_procedures_run?: number;
  };
  procedures_passed: number;
  total_procedures: number;
  pass_rate_pct: number;
  critical_failures_count: number;
  assertions_summary: Record<string, any>;
  procedure_log: VerificationProcedure[];
}

export interface ForensicScore {
  z_score?: number;
  m_score?: number;
  zone?: string;
  risk_level?: string;
  status?: string;
  sloan_accrual_ratio?: string;
  earnings_quality?: string;
  roe_calculated?: string;
  "3_stage_dupont"?: {
    net_profit_margin: string;
    asset_turnover: number;
    equity_multiplier: number;
  };
  "5_stage_dupont"?: {
    tax_burden: number;
    interest_burden: number;
    operating_margin: string;
    asset_turnover: number;
    equity_multiplier: number;
  };
}

export interface AnalyticsData {
  ratios?: Array<{
    rule_id: string;
    category: string;
    ratio_name: string;
    formula: string;
    value: number;
    formatted: string;
  }>;
  disconnects?: Array<{
    rule_id: string;
    rule_name: string;
    status: 'PASS' | 'WARNING' | 'FAIL';
    explanation: string;
  }>;
  analysis_table?: Array<Record<string, any>>;
  forensics?: {
    altman_z_score?: ForensicScore;
    beneish_m_score?: ForensicScore;
    sloan_accrual_ratio?: ForensicScore;
    dupont_roe_breakdown?: ForensicScore;
    benford_law_analysis?: Record<string, any>;
  };
}

export interface ForecastData {
  driver_based_model?: Array<Record<string, any>>;
  holt_winters?: Record<string, any>;
  arima_sarimax?: Record<string, any>;
  monte_carlo_simulation?: {
    base_revenue?: number;
    percentiles_final_year?: {
      revenue?: Record<string, number>;
      operating_income?: Record<string, number>;
    };
    value_at_risk_95?: number;
  };
}

export interface DeliverablesData {
  pdf_report_url?: string;
  excel_workbook_url?: string;
  pdf_storage_path?: string;
  excel_storage_path?: string;
  audit_status?: AuditStatus;
}

export interface AuditResult {
  id: string;
  project_id: string;
  verification_data?: VerificationData;
  analytics_data?: AnalyticsData;
  forensics_data?: AnalyticsData['forensics'];
  forecast_data?: ForecastData;
  deliverables?: DeliverablesData;
  created_at: string;
}
