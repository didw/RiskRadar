import { readFileSync } from 'fs';
import { join, dirname } from 'path';
import { fileURLToPath } from 'url';
import { gql } from 'graphql-tag';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

const loadGraphQLFile = (filename: string): string => {
  return readFileSync(join(__dirname, filename), 'utf-8');
};

const baseTypeDefs = loadGraphQLFile('base.graphql');
const companyTypeDefs = loadGraphQLFile('company.graphql');
const riskTypeDefs = loadGraphQLFile('risk.graphql');
const userTypeDefs = loadGraphQLFile('user.graphql');
const newsTypeDefs = loadGraphQLFile('news.graphql');
const subscriptionTypeDefs = loadGraphQLFile('subscription.graphql');

export const typeDefs = gql`
  ${baseTypeDefs}
  ${companyTypeDefs}
  ${riskTypeDefs}
  ${userTypeDefs}
  ${newsTypeDefs}
  ${subscriptionTypeDefs}
`;