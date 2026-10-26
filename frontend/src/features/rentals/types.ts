/**
 * Rental Request and Central State Machine types.
 * Strictly adheres to AGENTS.md Rule 14 (Allowed transitions) and Rule 21 (Idempotent sync).
 */

export type RentalStatus = 'pending' | 'accepted' | 'rejected' | 'cancelled' | 'completed';

export interface RentalRequestItem {
  id: string;
  equipmentId: string;
  renterId: string;
  rentalDate: string;
  selectedDates?: string | string[] | null;
  durationUnits: number;
  totalEstimatedPrice: number;
  status: RentalStatus;
  note?: string | null;
  idempotencyKey?: string | null;
  createdAt: string;
}

export interface RentalRequestCreateInput {
  equipmentId: string;
  rentalDate: string;
  selectedDates?: string[];
  durationUnits: number;
  note?: string;
  idempotencyKey?: string;
}

export interface RentalStatusUpdateInput {
  targetStatus: RentalStatus;
}
