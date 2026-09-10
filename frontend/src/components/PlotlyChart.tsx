'use client';

import React from 'react';
import dynamic from 'next/dynamic';

// Dynamically import Plotly with SSR disabled for Next.js App Router compatibility
const Plot = dynamic(() => import('react-plotly.js'), { ssr: false });

interface PlotlyChartProps {
  data: any[];
  layout?: Record<string, any>;
  config?: Record<string, any>;
  style?: React.CSSProperties;
  className?: string;
}

export default function PlotlyChart({ data, layout, config, style, className }: PlotlyChartProps) {
  const defaultLayout = {
    autosize: true,
    bargap: 0.28,
    bargroupgap: 0.08,
    margin: { t: 30, r: 25, l: 55, b: 45 },
    paper_bgcolor: 'transparent',
    plot_bgcolor: 'transparent',
    font: { family: 'Inter, ui-sans-serif, system-ui, sans-serif', size: 13, color: '#0F172A' },
    hoverlabel: { 
      bgcolor: '#0F172A', 
      bordercolor: '#0F172A', 
      font: { color: '#FFFFFF', family: 'Inter', size: 12 } 
    },
    xaxis: {
      gridcolor: '#F1F5F9',
      zerolinecolor: '#E2E8F0',
      tickfont: { color: '#0F172A', size: 12, family: 'Inter' },
      titlefont: { color: '#0F172A', size: 12, family: 'Inter' },
    },
    yaxis: {
      gridcolor: '#F1F5F9',
      zerolinecolor: '#E2E8F0',
      tickfont: { color: '#0F172A', size: 12, family: 'Inter' },
      titlefont: { color: '#0F172A', size: 12, family: 'Inter' },
    },
    legend: {
      font: { color: '#0F172A', size: 12, family: 'Inter' },
      bgcolor: 'rgba(255, 255, 255, 0.95)',
      bordercolor: '#E2E8F0',
      borderwidth: 1,
    },
    ...layout,
  };

  const defaultConfig = {
    responsive: true,
    displayModeBar: false,
    ...config,
  };

  return (
    <div className={className || "w-full h-[350px] min-h-[320px]"}>
      <Plot
        data={data || []}
        layout={defaultLayout}
        config={defaultConfig}
        style={style || { width: '100%', height: '100%' }}
        useResizeHandler={true}
      />
    </div>
  );
}

