/**
 * Shared TypeScript types for the entire frontend.
 */

export interface TranscriptEntry {
  id?: string;
  speaker: 'customer' | 'agent' | 'system';
  text: string;
  timestamp: string;
}

export interface KnowledgeChunk {
  content: string;
  source: string;
  file: string;
  score: number;
}

export interface ToolCallRecord {
  tool_name: string;
  parameters: Record<string, unknown>;
  result: Record<string, unknown>;
  success: boolean;
}

export interface CustomerInfo {
  id: string;
  name: string;
  email: string;
  phone?: string;
  account_status: string;
  membership_tier: string;
  join_date?: string;
  total_orders?: number;
}

export interface OrderInfo {
  order_id?: string;
  id?: string;
  product_name: string;
  status: string;
  amount: number;
  order_date: string;
  estimated_delivery?: string;
  tracking_number?: string;
  carrier?: string;
  shipping_address?: string;
  available_options?: string[];
}

export interface AgentAnalysis {
  intent: string;
  intent_confidence: number;
  sentiment: string;
  sentiment_confidence: number;
  conversation_stage: string;
  key_entities: string[];
  next_best_action: string;
  action_priority: string;
  action_rationale: string;
  suggested_response: string;
  retrieved_knowledge: KnowledgeChunk[];
  tool_calls_made: ToolCallRecord[];
  customer_info?: CustomerInfo | null;
  order_info?: OrderInfo | null;
  error?: string | null;
}

export interface CallSummary {
  issue: string;
  intent: string;
  resolution: string;
  actions_taken: string[];
  follow_up_required: boolean;
  follow_up_description?: string;
  customer_sentiment_overall: string;
  escalated: boolean;
  escalation_reason?: string;
  key_information: string[];
}

export type CallStatus = 'idle' | 'active' | 'analyzing' | 'generating_summary' | 'ended';

export type ConnectionStatus = 'disconnected' | 'connecting' | 'connected' | 'error';
