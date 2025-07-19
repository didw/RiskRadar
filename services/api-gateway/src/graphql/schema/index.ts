import { readFileSync } from 'fs';
import { join } from 'path';
import { gql } from 'graphql-tag';

const loadGraphQLFile = (filename: string): string => {
  return readFileSync(join(__dirname, filename), 'utf-8');
};

const baseTypeDefs = loadGraphQLFile('base.graphql');
const companyTypeDefs = loadGraphQLFile('company.graphql');
const riskTypeDefs = loadGraphQLFile('risk.graphql');
const userTypeDefs = loadGraphQLFile('user.graphql');
const newsTypeDefs = loadGraphQLFile('news.graphql');

export const typeDefs = gql`
  ${baseTypeDefs}
  ${companyTypeDefs}
  ${riskTypeDefs}
  ${userTypeDefs}
  ${newsTypeDefs}
`;