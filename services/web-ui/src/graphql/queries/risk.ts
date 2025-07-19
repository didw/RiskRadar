import { gql } from '@apollo/client';

export const GET_RISK_OVERVIEW = gql`
  query GetRiskOverview($companyId: ID, $dateRange: DateRangeInput) {
    riskOverview(companyId: $companyId, dateRange: $dateRange) {
      totalScore
      trend
      changePercent
      metrics {
        id
        name
        value
        change
        changePercent
        trend
        icon
      }
      chartData {
        date
        average
        high
        medium
        low
      }
    }
  }
`;

export const GET_RISK_DISTRIBUTION = gql`
  query GetRiskDistribution($filterBy: String) {
    riskDistribution(filterBy: $filterBy) {
      byLevel {
        level
        count
        percentage
      }
      byIndustry {
        industry
        low
        medium
        high
      }
    }
  }
`;

export const GET_RISK_METRICS = gql`
  query GetRiskMetrics {
    riskMetrics {
      id
      title
      value
      change
      changeLabel
      trend
      icon
      variant
    }
  }
`;

export const GET_COMPANY_RISKS = gql`
  query GetCompanyRisks(
    $filter: CompanyRiskFilter
    $sort: CompanyRiskSort
    $pagination: PaginationInput
  ) {
    companyRisks(filter: $filter, sort: $sort, pagination: $pagination) {
      items {
        id
        name
        industry
        riskScore
        riskLevel
        change
        marketCap
        lastUpdated
      }
      totalCount
      pageInfo {
        hasNextPage
        hasPreviousPage
        currentPage
        totalPages
      }
    }
  }
`;

export const RISK_UPDATE_SUBSCRIPTION = gql`
  subscription OnRiskUpdate($companyId: ID) {
    riskUpdate(companyId: $companyId) {
      companyId
      riskScore
      riskLevel
      change
      timestamp
    }
  }
`;