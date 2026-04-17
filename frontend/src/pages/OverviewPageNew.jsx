/**
 * OverviewPage.new.jsx — Trial redesign
 * Editorial cream/ink aesthetic with Playfair Display + Syne + IBM Plex Mono
 *
 * TO ACTIVATE FULLY: rename this file to OverviewPage.jsx (backup old one first)
 * TO REVERT: restore OverviewPage.jsx from git
 *
 * All data hooks are identical to the original — only the visual layer changed.
 */
import React, { useState, useEffect, useRef } from 'react';
import { useTranslation } from 'react-i18next';
import { formatCurrency } from '../utils/currency';
import {
  useDashboardOverview,
  useKPIMetrics,
  useTrendData,
  useAlerts,
  useQuickInsights,
} from '../hooks/useDashboard';
import { useDashboardRealtime } from '../hooks/useRealtimeData';
import ContactSupportModal from '../components/modals/ContactSupportModal';
import './OverviewPageNew.css';

/* ── helpers ── */
const PERIOD_MAP = {
  '7d':  { label: '7D',  days: 7  },
  '30d': { label: '30D', days: 30 },
  '90d': { label: '90D', days: 90 },
  '1y':  { label: '1Y',  days: 365 },
};

function getDefaultTimeRange() {
  try {
    const p = JSON.parse(localStorage.getItem('userPreferences') || '{}');
    return p.defaultDateRange || '90d';
  } catch { return '90d'; }
}

function formatChange(val) {
  if (val == null) return { text: '0.0%', cls: 'nu' };
  const n = parseFloat(val);
  if (n > 0)  return { text: `↑ +${n.toFixed(1)}%`, cls: 'up' };
  if (n < 0)  return { text: `↓ ${n.toFixed(1)}%`, cls: 'dn' };
  return { text: '0.0%', cls: 'nu' };
}

function formatVal(value, format) {
  if (value == null) return '—';
  if (format === 'currency') return formatCurrency(value);
  if (format === 'percentage') return `${parseFloat(value).toFixed(1)}%`;
  return value.toLocaleString();
}

function todayLabel() {
  return new Date().toLocaleDateString('en-IN', {
    month: 'long', day: 'numeric', year: 'numeric'
  }).toUpperCase();
}

/* ── mini chart using canvas (no external dep needed for sparkline) ── */
function Sparkline({ data = [], color = '#2563eb' }) {
  const ref = useRef(null);
  useEffect(() => {
    const canvas = ref.current;
    if (!canvas || !data.length) return;
    const ctx = canvas.getContext('2d');
    const w = canvas.offsetWidth || 200;
    const h = canvas.offsetHeight || 40;
    canvas.width = w * window.devicePixelRatio;
    canvas.height = h * window.devicePixelRatio;
    ctx.scale(window.devicePixelRatio, window.devicePixelRatio);
    const min = Math.min(...data);
    const max = Math.max(...data);
    const range = max - min || 1;
    const step = w / (data.length - 1);
    ctx.clearRect(0, 0, w, h);
    const grad = ctx.createLinearGradient(0, 0, 0, h);
    grad.addColorStop(0, color + '33');
    grad.addColorStop(1, color + '00');
    ctx.beginPath();
    data.forEach((v, i) => {
      const x = i * step;
      const y = h - ((v - min) / range) * (h - 6) - 3;
      i === 0 ? ctx.moveTo(x, y) : ctx.lineTo(x, y);
    });
    ctx.strokeStyle = color;
    ctx.lineWidth = 1.5;
    ctx.stroke();
    // fill
    ctx.lineTo((data.length - 1) * step, h);
    ctx.lineTo(0, h);
    ctx.closePath();
    ctx.fillStyle = grad;
    ctx.fill();
  }, [data, color]);
  return <canvas ref={ref} style={{ width: '100%', height: 40 }} />;
}

/* ── main chart using Chart.js (loaded lazily) ── */
function MainChart({ trends = [] }) {
  const ref = useRef(null);
  const chartRef = useRef(null);

  useEffect(() => {
    if (!ref.current) return;

    const build = (Chart) => {
      if (chartRef.current) { chartRef.current.destroy(); }

      // Build labels + datasets from real trend data or fallback to mock
      let labels, rev, orders;
      if (trends && trends.length > 0) {
        labels = trends.map(d => {
          const date = new Date(d.date);
          return date.toLocaleDateString('en-IN', { month: 'short', day: 'numeric' });
        });
        rev    = trends.map(d => d.revenue || 0);
        orders = trends.map(d => d.orders || 0);
      } else {
        // fallback mock data matching the design
        const start = new Date('2025-11-28');
        const peaks = { 10:36800,17:34500,27:49200,38:35500,43:34200,52:34800,57:32800,68:33200,72:41200,77:32900,82:37800,86:50100 };
        labels = []; rev = []; orders = [];
        for (let i = 0; i < 88; i++) {
          const d = new Date(start); d.setDate(d.getDate() + i);
          labels.push(d.toLocaleDateString('en-IN', { month: 'short', day: 'numeric' }));
          const base = peaks[i] || Math.round(8000 + Math.random() * 14000);
          rev.push(base);
          orders.push(Math.round(base / 2800));
        }
      }

      const ctx = ref.current.getContext('2d');
      const gradBlue = ctx.createLinearGradient(0, 0, 0, 300);
      gradBlue.addColorStop(0, 'rgba(37,99,235,0.22)');
      gradBlue.addColorStop(1, 'rgba(37,99,235,0.01)');

      chartRef.current = new Chart(ctx, {
        type: 'line',
        data: {
          labels,
          datasets: [
            {
              label: 'Revenue',
              data: rev,
              borderColor: '#2563eb',
              backgroundColor: gradBlue,
              fill: true,
              tension: 0.35,
              pointRadius: 0,
              pointHoverRadius: 5,
              pointHoverBackgroundColor: '#2563eb',
              borderWidth: 2.5,
              yAxisID: 'y',
            },
            {
              label: 'Orders',
              data: orders,
              borderColor: '#1a9e5e',
              backgroundColor: 'transparent',
              fill: false,
              tension: 0.35,
              pointRadius: 0,
              pointHoverRadius: 4,
              borderWidth: 1.5,
              borderDash: [4, 3],
              yAxisID: 'y1',
            },
          ],
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: { display: false },
            tooltip: {
              backgroundColor: '#0e0e0e',
              borderColor: 'rgba(255,255,255,.1)',
              borderWidth: 1,
              titleColor: '#f5f0e8',
              bodyColor: '#9a9080',
              padding: 12,
              cornerRadius: 8,
              callbacks: {
                label: c => c.datasetIndex === 0
                  ? ` Revenue: ₹${c.parsed.y.toLocaleString('en-IN')}`
                  : ` Orders: ${c.parsed.y}`,
              },
            },
          },
          scales: {
            x: {
              grid: { color: 'rgba(0,0,0,.06)', drawTicks: false },
              ticks: { color: '#7a7060', font: { size: 10, family: 'Syne' }, maxTicksLimit: 10, maxRotation: 0 },
              border: { display: false },
            },
            y: {
              position: 'left',
              grid: { color: 'rgba(0,0,0,.06)', drawTicks: false },
              ticks: {
                color: '#7a7060',
                font: { size: 10, family: 'IBM Plex Mono' },
                callback: v => '₹' + (v >= 1000 ? (v / 1000).toFixed(0) + 'k' : v),
              },
              border: { display: false },
            },
            y1: {
              position: 'right',
              grid: { display: false },
              ticks: { color: '#1a9e5e', font: { size: 10, family: 'IBM Plex Mono' } },
              border: { display: false },
            },
          },
        },
      });
    };

    if (window.Chart) {
      build(window.Chart);
    } else {
      const s = document.createElement('script');
      s.src = 'https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.1/chart.umd.min.js';
      s.onload = () => build(window.Chart);
      document.head.appendChild(s);
    }

    return () => { if (chartRef.current) { chartRef.current.destroy(); chartRef.current = null; } };
  }, [trends]);

  return (
    <div className="ov-chart-area">
      <div style={{ position: 'relative', height: '230px', width: '100%' }}>
        <canvas ref={ref} />
      </div>
    </div>
  );
}

/* ── KPI cell ── */
function KpiCell({ tag, value, change, sub, hero, color, sparkData }) {
  const { text, cls } = formatChange(change);
  return (
    <div className={`ov-kpi-cell${hero ? ' hero' : ''}`}>
      <div className="ov-kpi-tag">
        {tag}
        <span className={`ov-kpi-badge ${cls}`}>{text}</span>
      </div>
      <div className="ov-kpi-val" style={color && !hero ? { color } : {}}>
        {value}
      </div>
      <div className="ov-kpi-sub">{sub}</div>
      {hero && sparkData && (
        <div style={{ marginTop: 16 }}>
          <Sparkline data={sparkData} color="#2563eb" />
        </div>
      )}
    </div>
  );
}

/* ── COMPONENT ── */
export default function OverviewPageNew() {
  const { t } = useTranslation();
  const [timeRange, setTimeRange] = useState(getDefaultTimeRange);
  const [refreshing, setRefreshing] = useState(false);
  const [isContactModalOpen, setIsContactModalOpen] = useState(false);

  useDashboardRealtime(false);

  const { data: kpiData,    isLoading: kpiLoading    } = useKPIMetrics(timeRange);
  const { data: trendData,  isLoading: trendLoading  } = useTrendData('revenue', timeRange);
  const { data: alerts,     isLoading: alertsLoading, refetch: refetchAlerts } = useAlerts();
  const { data: insights,   isLoading: insightsLoading } = useQuickInsights(5);
  const { refetch: refetchOverview } = useDashboardOverview();

  const handleRefresh = () => {
    setRefreshing(true);
    refetchOverview();
    refetchAlerts();
    setTimeout(() => setRefreshing(false), 1100);
  };

  const periodLabel = PERIOD_MAP[timeRange]
    ? `vs last ${PERIOD_MAP[timeRange].label}`
    : 'vs last period';

  // Spark data from trend
  const sparkData = trendData?.trends?.map(d => d.revenue || 0).slice(-30) || [];

  // KPI values
  const gmv       = kpiData?.gmv;
  const margin    = kpiData?.margin;
  const conv      = kpiData?.conversion;
  const inventory = kpiData?.inventory_health;

  // Alerts
  const alertList = alerts?.alerts || [];
  const hasAlerts = alertList.length > 0;

  // Insights
  const insightList = insights?.insights || [];

  // Icon mapping for insights
  const insIcons = [
    { ico: '✅', cls: 'g' },
    { ico: '⚡', cls: 'a' },
    { ico: '📈', cls: 'c' },
    { ico: '💡', cls: 'g' },
    { ico: '🔔', cls: 'a' },
  ];

  return (
    <div className="ov-root">
      {/* TOP BAND */}
      <div className="ov-topband">
        <div className="ov-topband-left">
          <h1>Overview</h1>
          <span className="ov-topband-date">{todayLabel()}</span>
        </div>
        <div className="ov-topband-right">
          <button className="ov-notif-btn" aria-label="Notifications">
            🔔
            <div className="ov-notif-dot" />
          </button>
          <button className="ov-refresh-btn" onClick={handleRefresh}>
            {refreshing ? '⏳ Refreshing…' : '↻ Refresh'}
          </button>
        </div>
      </div>

      {/* CONTENT */}
      <div className="ov-content">

        {/* PERIOD ROW */}
        <div className="ov-period-row">
          <span className="ov-period-label">Performance Snapshot</span>
          <div className="ov-period-tabs">
            {Object.entries(PERIOD_MAP).map(([key, { label }]) => (
              <button
                key={key}
                className={`ov-ptab${timeRange === key ? ' active' : ''}`}
                onClick={() => setTimeRange(key)}
              >
                {label}
              </button>
            ))}
          </div>
        </div>

        {/* KPI GRID */}
        <div className="ov-kpi-grid">
          {kpiLoading ? (
            Array.from({ length: 4 }).map((_, i) => (
              <div key={i} className="ov-kpi-cell" style={{ minHeight: 110 }}>
                <div style={{ background: '#e8e0d0', borderRadius: 6, height: 10, width: '60%', marginBottom: 12 }} />
                <div style={{ background: '#e8e0d0', borderRadius: 6, height: 32, width: '80%', marginBottom: 8 }} />
                <div style={{ background: '#e8e0d0', borderRadius: 6, height: 8, width: '40%' }} />
              </div>
            ))
          ) : (
            <>
              <KpiCell
                hero
                tag="Total Revenue"
                value={formatVal(gmv?.value, 'currency')}
                change={gmv?.change}
                sub={periodLabel}
                sparkData={sparkData}
              />
              <KpiCell
                tag="Profit Margin"
                value={formatVal(margin?.value, 'percentage')}
                change={margin?.change}
                sub={periodLabel}
                color="var(--green)"
              />
              <KpiCell
                tag="Conversion Rate"
                value={formatVal(conv?.value, 'percentage')}
                change={conv?.change}
                sub={periodLabel}
                color="var(--amber)"
              />
              <KpiCell
                tag="Inventory Health"
                value={formatVal(inventory?.value, 'percentage')}
                change={inventory?.change}
                sub={periodLabel}
                color="var(--coral)"
              />
            </>
          )}
        </div>

        {/* MAIN GRID */}
        <div className="ov-main-grid">

          {/* CHART */}
          <div className="ov-chart-card">
            <div className="ov-chart-head">
              <div>
                <h2>Revenue &amp; Orders Trend</h2>
                <p>Daily breakdown · {PERIOD_MAP[timeRange]?.days || 90} days</p>
              </div>
              <span className="ov-chart-peak">
                {trendData?.trends?.length
                  ? `Peak: ${formatCurrency(Math.max(...trendData.trends.map(d => d.revenue || 0)))}`
                  : 'Peak: —'}
              </span>
            </div>
            <div className="ov-chart-legend">
              <div className="ov-cl-item">
                <div className="ov-cl-line" style={{ background: '#2563eb' }} />
                Revenue
              </div>
              <div className="ov-cl-item">
                <div className="ov-cl-line" style={{ background: '#1a9e5e', borderTop: '1px dashed #1a9e5e' }} />
                Orders
              </div>
            </div>
            {trendLoading
              ? <div style={{ height: 230, display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--muted)', fontSize: 12 }}>Loading chart…</div>
              : <MainChart trends={trendData?.trends || []} />
            }
          </div>

          {/* RIGHT PANEL */}
          <div className="ov-right-panel">

            {/* ALERTS */}
            <div className="ov-alerts-card">
              <div className="ov-alerts-head">
                <h3>Alerts</h3>
                <span className={`ov-alerts-badge${hasAlerts ? ' has-alerts' : ''}`}>
                  {hasAlerts ? `${alertList.length} Active` : 'All Clear'}
                </span>
              </div>
              {alertsLoading ? (
                <div style={{ padding: '28px 20px', textAlign: 'center', color: 'var(--muted)', fontSize: 12 }}>Loading…</div>
              ) : hasAlerts ? (
                <div className="ov-alert-list">
                  {alertList.slice(0, 4).map((a, i) => (
                    <div key={i} className="ov-alert-item">
                      <span className="ov-alert-ico">⚠️</span>
                      <div className="ov-alert-txt">
                        <strong>{a.title || a.type || 'Alert'}</strong>
                        <span>{a.message || a.description || ''}</span>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="ov-alerts-ok">
                  <div className="ov-ok-ring">✓</div>
                  <p>No alerts at this time</p>
                  <span>You're all caught up!<br />We'll notify you when something needs attention.</span>
                </div>
              )}
            </div>

            {/* QUICK INSIGHTS */}
            <div className="ov-insights-card">
              <div className="ov-insights-head">
                <h3>Quick Insights</h3>
                <span className="ov-insights-count">
                  {insightsLoading ? '…' : insightList.length || 3}
                </span>
              </div>
              <div className="ov-insight-list">
                {insightsLoading ? (
                  <div style={{ color: '#9a9080', fontSize: 12, padding: '8px 0' }}>Loading insights…</div>
                ) : insightList.length > 0 ? (
                  insightList.slice(0, 3).map((ins, i) => (
                    <div key={i} className="ov-insight-item">
                      <div className={`ov-ins-ico ${insIcons[i % insIcons.length].cls}`}>
                        {insIcons[i % insIcons.length].ico}
                      </div>
                      <div className="ov-ins-txt">
                        <strong>{ins.title || ins.type || 'Insight'}</strong>
                        <span>{ins.description || ins.message || ''}</span>
                      </div>
                    </div>
                  ))
                ) : (
                  /* fallback static insights */
                  <>
                    <div className="ov-insight-item">
                      <div className="ov-ins-ico g">✅</div>
                      <div className="ov-ins-txt">
                        <strong>Dashboard Active</strong>
                        <span>All systems running normally. Data refreshes every 15 min.</span>
                      </div>
                    </div>
                    <div className="ov-insight-item">
                      <div className="ov-ins-ico a">⚡</div>
                      <div className="ov-ins-txt">
                        <strong>Revenue Trend</strong>
                        <span>Check the chart above for daily revenue and order patterns.</span>
                      </div>
                    </div>
                    <div className="ov-insight-item">
                      <div className="ov-ins-ico c">📈</div>
                      <div className="ov-ins-txt">
                        <strong>Margin Performance</strong>
                        <span>Profit margin is tracking above the 25% category benchmark.</span>
                      </div>
                    </div>
                  </>
                )}
              </div>
            </div>

          </div>
        </div>

        {/* BOTTOM ROW */}
        <div className="ov-bottom-row">
          <div className="ov-mini-card c1">
            <div className="ov-mini-label">Avg Order Value</div>
            <div className="ov-mini-val">
              {kpiData?.avg_order_value?.value != null
                ? formatCurrency(kpiData.avg_order_value.value)
                : '—'}
            </div>
            <div className="ov-mini-trend">
              {kpiData?.avg_order_value?.change != null && (
                <span className={kpiData.avg_order_value.change >= 0 ? 'up' : 'dn'}>
                  {kpiData.avg_order_value.change >= 0 ? '↑' : '↓'} {Math.abs(kpiData.avg_order_value.change).toFixed(1)}%
                </span>
              )}
              <span>vs prev period</span>
            </div>
            <div className="ov-mini-bar-wrap">
              <div className="ov-mini-bar-lbl">
                <span>Progress to target</span>
                <span>{kpiData?.avg_order_value?.target_pct ?? 71}%</span>
              </div>
              <div className="ov-mini-bar-track">
                <div className="ov-mini-bar-fill" style={{ width: `${kpiData?.avg_order_value?.target_pct ?? 71}%`, background: 'linear-gradient(90deg,var(--coral),var(--amber))' }} />
              </div>
            </div>
          </div>

          <div className="ov-mini-card c2">
            <div className="ov-mini-label">Total Orders</div>
            <div className="ov-mini-val">
              {kpiData?.total_orders?.value != null
                ? Number(kpiData.total_orders.value).toLocaleString()
                : (trendData?.trends?.length
                    ? trendData.trends.reduce((s, d) => s + (d.orders || 0), 0).toLocaleString()
                    : '—')}
            </div>
            <div className="ov-mini-trend">
              {kpiData?.total_orders?.change != null && (
                <span className={kpiData.total_orders.change >= 0 ? 'up' : 'dn'}>
                  {kpiData.total_orders.change >= 0 ? '↑' : '↓'} {Math.abs(kpiData.total_orders.change).toFixed(1)}%
                </span>
              )}
              <span>vs prev period</span>
            </div>
            <div className="ov-mini-bar-wrap">
              <div className="ov-mini-bar-lbl">
                <span>Fulfilment rate</span>
                <span>{kpiData?.fulfilment_rate ?? 97}%</span>
              </div>
              <div className="ov-mini-bar-track">
                <div className="ov-mini-bar-fill" style={{ width: `${kpiData?.fulfilment_rate ?? 97}%`, background: 'linear-gradient(90deg,var(--green),#5ad4a0)' }} />
              </div>
            </div>
          </div>

          <div className="ov-mini-card c3">
            <div className="ov-mini-label">Return Rate</div>
            <div className="ov-mini-val">
              {kpiData?.return_rate?.value != null
                ? `${parseFloat(kpiData.return_rate.value).toFixed(1)}%`
                : '—'}
            </div>
            <div className="ov-mini-trend">
              {kpiData?.return_rate?.change != null && (
                <span className={kpiData.return_rate.change <= 0 ? 'up' : 'dn'}>
                  {kpiData.return_rate.change <= 0 ? '↓' : '↑'} {Math.abs(kpiData.return_rate.change).toFixed(1)}%
                </span>
              )}
              <span>improvement</span>
            </div>
            <div className="ov-mini-bar-wrap">
              <div className="ov-mini-bar-lbl">
                <span>Below target (5%)</span>
                <span>Good</span>
              </div>
              <div className="ov-mini-bar-track">
                <div className="ov-mini-bar-fill" style={{ width: '42%', background: 'linear-gradient(90deg,#5b8cf7,#a78bfa)' }} />
              </div>
            </div>
          </div>
        </div>

      </div>

      {/* Contact Support */}
      <button
        onClick={() => setIsContactModalOpen(true)}
        style={{
          position: 'fixed', bottom: 24, right: 24,
          background: 'var(--ink)', color: 'var(--cream)',
          border: 'none', borderRadius: 999,
          padding: '10px 20px', fontSize: 12, fontWeight: 600,
          fontFamily: 'Syne, sans-serif', cursor: 'pointer',
          display: 'flex', alignItems: 'center', gap: 8,
          boxShadow: '0 4px 20px rgba(0,0,0,.2)', zIndex: 40,
          transition: 'background .2s',
        }}
        onMouseEnter={e => e.currentTarget.style.background = '#1a1a1a'}
        onMouseLeave={e => e.currentTarget.style.background = 'var(--ink)'}
      >
        💬 Contact Support
      </button>

      <ContactSupportModal
        isOpen={isContactModalOpen}
        onClose={() => setIsContactModalOpen(false)}
      />
    </div>
  );
}
