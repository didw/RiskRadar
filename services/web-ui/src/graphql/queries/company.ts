import { gql } from '@apollo/client';

export const GET_COMPANY = gql`
  query GetCompany($id: ID!) {
    company(id: $id) {
      id
      name
      industry
      description
      foundedYear
      marketCap
      employeeCount
      website
      logo
      riskProfile {
        score
        level
        trend
        lastUpdated
        factors {
          id
          name
          score
          weight
          description
        }
      }
    }
  }
`;

export const GET_COMPANIES = gql`
  query GetCompanies($filter: CompanyFilter, $sort: CompanySort) {
    companies(filter: $filter, sort: $sort) {
      id
      name
      industry
      riskScore
      riskLevel
      change
      marketCap
      lastUpdated
    }
  }
`;

export const GET_TOP_COMPANIES = gql`
  query GetTopCompanies($limit: Int = 10) {
    topCompanies(limit: $limit) {
      id
      name
      industry
      riskScore
    }
  }
`;

export const SEARCH_COMPANIES = gql`
  query SearchCompanies($query: String!, $limit: Int = 10) {
    searchCompanies(query: $query, limit: $limit) {
      id
      name
      industry
      riskScore
      matchScore
    }
  }
`;