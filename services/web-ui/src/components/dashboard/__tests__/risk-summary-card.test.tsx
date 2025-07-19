import { render, screen } from '@testing-library/react';
import { RiskSummaryCard } from '../risk-summary-card';
import { TrendingUp } from 'lucide-react';

describe('RiskSummaryCard', () => {
  it('renders with required props', () => {
    render(
      <RiskSummaryCard
        title="Test Card"
        value="100"
      />
    );
    
    expect(screen.getByText('Test Card')).toBeInTheDocument();
    expect(screen.getByText('100')).toBeInTheDocument();
  });

  it('renders with all props', () => {
    render(
      <RiskSummaryCard
        title="Test Card"
        value={100}
        change={10}
        changeLabel="% increase"
        icon={<TrendingUp />}
        trend="up"
        variant="success"
      />
    );
    
    expect(screen.getByText('Test Card')).toBeInTheDocument();
    expect(screen.getByText('100')).toBeInTheDocument();
    expect(screen.getByText('+10% increase')).toBeInTheDocument();
  });

  it('handles negative change correctly', () => {
    render(
      <RiskSummaryCard
        title="Test Card"
        value="50"
        change={-5}
        changeLabel="% decrease"
        trend="down"
      />
    );
    
    expect(screen.getByText('-5% decrease')).toBeInTheDocument();
  });

  it('applies correct variant classes', () => {
    const { container } = render(
      <RiskSummaryCard
        title="Danger Card"
        value="High"
        variant="danger"
      />
    );
    
    const card = container.querySelector('[class*="border-red"]');
    expect(card).toBeInTheDocument();
  });
});