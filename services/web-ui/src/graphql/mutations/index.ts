import { gql } from '@apollo/client';

export const UPDATE_COMPANY_ALERT = gql`
  mutation UpdateCompanyAlert($companyId: ID!, $alertSettings: AlertSettingsInput!) {
    updateCompanyAlert(companyId: $companyId, alertSettings: $alertSettings) {
      id
      companyId
      enabled
      thresholds {
        riskScore
        changePercent
      }
      channels {
        email
        sms
        push
      }
    }
  }
`;

export const CREATE_RISK_REPORT = gql`
  mutation CreateRiskReport($companyId: ID!, $reportType: ReportType!) {
    createRiskReport(companyId: $companyId, reportType: $reportType) {
      id
      reportUrl
      generatedAt
      expiresAt
    }
  }
`;

export const EXPORT_RISK_DATA = gql`
  mutation ExportRiskData($filter: RiskDataFilter!, $format: ExportFormat!) {
    exportRiskData(filter: $filter, format: $format) {
      downloadUrl
      expiresAt
    }
  }
`;