export interface Ticket {
  id: number;
  ticket_no: string;
  maxis_centre_id: number;
  category: 'Signal Loss' | 'Hardware Crash' | 'Screen Damage' | 'Maintenance';
  priority: 'Low' | 'Medium' | 'High' | 'Critical';
  status: 'open' | 'assigned' | 'in_progress' | 'resolved' | 'closed';
  description: string;
}