/**
 * CustomerInfo — displays customer and order information in the side panel.
 */
import { useEffect, useState } from 'react';
import { api } from '../services/api';
import type { AgentAnalysis, CustomerInfo as CustomerInfoType, OrderInfo } from '../types';

interface Props {
  customerId: string | null;
  analysis: AgentAnalysis | null;
}

export function CustomerInfo({ customerId, analysis }: Props) {
  const [customer, setCustomer] = useState<CustomerInfoType | null>(null);

  // Load customer data when ID is available
  useEffect(() => {
    if (!customerId) return;
    api.getCustomer(customerId)
      .then((c) => setCustomer(c as unknown as CustomerInfoType))
      .catch(() => {});
  }, [customerId]);

  // Prefer analysis-provided customer info (richer, from tool call)
  const displayCustomer = analysis?.customer_info || customer;
  const displayOrder = analysis?.order_info as OrderInfo | null | undefined;

  return (
    <>
      {/* Customer Section */}
      <div className="panel-section">
        <div className="panel-section-header">
          <span className="panel-section-title">Customer</span>
          {displayCustomer && (
            <span className={`status-chip ${displayCustomer.account_status}`}>
              {displayCustomer.account_status}
            </span>
          )}
        </div>

        {displayCustomer ? (
          <div className="customer-info-grid">
            <div className="customer-field" style={{ gridColumn: '1 / -1' }}>
              <span className="customer-field-label">Name</span>
              <span className="customer-field-value" style={{ fontSize: '0.9rem', fontWeight: 600 }}>
                {displayCustomer.name}
              </span>
            </div>
            <div className="customer-field">
              <span className="customer-field-label">ID</span>
              <span className="customer-field-value" style={{ fontFamily: 'var(--font-mono)', fontSize: '0.75rem' }}>
                {displayCustomer.id}
              </span>
            </div>
            <div className="customer-field">
              <span className="customer-field-label">Tier</span>
              <span className={`status-chip ${displayCustomer.membership_tier}`}>
                {displayCustomer.membership_tier}
              </span>
            </div>
            {displayCustomer.email && (
              <div className="customer-field" style={{ gridColumn: '1 / -1' }}>
                <span className="customer-field-label">Email</span>
                <span className="customer-field-value text-secondary" style={{ fontSize: '0.75rem' }}>
                  {displayCustomer.email}
                </span>
              </div>
            )}
            {displayCustomer.phone && (
              <div className="customer-field">
                <span className="customer-field-label">Phone</span>
                <span className="customer-field-value" style={{ fontSize: '0.75rem' }}>
                  {displayCustomer.phone}
                </span>
              </div>
            )}
            {displayCustomer.total_orders !== undefined && (
              <div className="customer-field">
                <span className="customer-field-label">Total Orders</span>
                <span className="customer-field-value">{displayCustomer.total_orders}</span>
              </div>
            )}
          </div>
        ) : customerId ? (
          <div className="empty-state" style={{ padding: '10px 0' }}>
            <div className="spinner" style={{ margin: '0 auto 6px' }} />
            <span>Loading customer data...</span>
          </div>
        ) : (
          <div className="empty-state" style={{ padding: '10px 0' }}>
            No customer selected. Customer info will appear after tool lookup.
          </div>
        )}
      </div>

      {/* Order Section */}
      {displayOrder && (
        <div className="panel-section">
          <div className="panel-section-header">
            <span className="panel-section-title">Order Details</span>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
            <div className="order-status-row">
              <div className={`order-status-dot ${(displayOrder.status || '').toLowerCase().replace(' ', '_')}`} />
              <div>
                <div style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-primary)' }}>
                  {displayOrder.product_name}
                </div>
                <div style={{ fontSize: '0.72rem', color: 'var(--text-secondary)' }}>
                  Status: <strong>{displayOrder.status?.replace(/_/g, ' ')}</strong>
                </div>
              </div>
            </div>

            <div className="customer-info-grid">
              <div className="customer-field">
                <span className="customer-field-label">Order ID</span>
                <span className="customer-field-value" style={{ fontFamily: 'var(--font-mono)', fontSize: '0.72rem' }}>
                  {displayOrder.order_id || displayOrder.id || '—'}
                </span>
              </div>
              <div className="customer-field">
                <span className="customer-field-label">Amount</span>
                <span className="customer-field-value">
                  ${displayOrder.amount?.toFixed(2)}
                </span>
              </div>
              {displayOrder.tracking_number && displayOrder.tracking_number !== 'Not yet assigned' && (
                <div className="customer-field" style={{ gridColumn: '1 / -1' }}>
                  <span className="customer-field-label">Tracking</span>
                  <span className="customer-field-value" style={{ fontFamily: 'var(--font-mono)', fontSize: '0.72rem' }}>
                    {displayOrder.tracking_number} ({displayOrder.carrier})
                  </span>
                </div>
              )}
              {displayOrder.estimated_delivery && (
                <div className="customer-field" style={{ gridColumn: '1 / -1' }}>
                  <span className="customer-field-label">Est. Delivery</span>
                  <span className="customer-field-value">{displayOrder.estimated_delivery}</span>
                </div>
              )}
            </div>

            {/* Resolution options */}
            {displayOrder.available_options && displayOrder.available_options.length > 0 && (
              <div style={{ marginTop: 4 }}>
                <div className="customer-field-label" style={{ marginBottom: 5 }}>Resolution Options</div>
                {displayOrder.available_options.map((opt, i) => (
                  <div
                    key={i}
                    style={{
                      fontSize: '0.75rem',
                      color: 'var(--text-secondary)',
                      padding: '3px 0',
                      borderBottom: i < displayOrder.available_options!.length - 1
                        ? '1px solid var(--color-border-subtle)'
                        : 'none',
                    }}
                  >
                    · {opt}
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}
    </>
  );
}
