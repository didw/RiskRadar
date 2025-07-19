import { NextResponse } from 'next/server';

export async function POST() {
  try {
    const response = await fetch('http://data-service:8001/simulate-news', {
      method: 'POST'
    });
    const data = await response.json();
    return NextResponse.json(data);
  } catch (error) {
    return NextResponse.json(
      { error: 'Failed to simulate news' },
      { status: 500 }
    );
  }
}