"use client";

import { useState, useEffect } from 'react';
import { Save, X } from 'lucide-react';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Label } from '@/components/ui/label';
import { DatePicker } from '@/components/ui/date-picker';
import axios from 'axios';

interface Event {
  id: string;
  academic_schedule_id: string;
  type_id: string;
  start_date: string;
  end_date?: string;
  event_type: string;
  semester_type: string;
}

interface SingleEventEditModalProps {
  event: Event | null;
  isOpen: boolean;
  onClose: () => void;
  onUpdate: () => void;
}

export function SingleEventEditModal({ event, isOpen, onClose, onUpdate }: SingleEventEditModalProps) {
  const [editingEvent, setEditingEvent] = useState<Event | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    if (event && isOpen) {
      setEditingEvent({ ...event });
    }
  }, [event, isOpen]);

  const formatDateForAPI = (date: Date) => {
    // Return ISO 8601 format for the new calendar_events table
    return date.toISOString();
  };

  const parseDate = (dateStr: string) => {
    if (!dateStr) return undefined;
    
    // Handle ISO 8601 format (e.g., "2025-02-16T00:00:00+04:00")
    if (dateStr.includes('T') || dateStr.includes('-')) {
      const date = new Date(dateStr);
      return isNaN(date.getTime()) ? undefined : date;
    }
    
    // Handle DD/MM/YYYY format (legacy)
    const [day, month, year] = dateStr.split('/');
    if (!day || !month || !year) return undefined;
    return new Date(parseInt(year), parseInt(month) - 1, parseInt(day));
  };

  const handleUpdateEvent = async () => {
    if (!editingEvent) return;

    setIsLoading(true);
    try {
      await axios.put(`http://localhost:8000/api/v1/academic-schedule/events/${editingEvent.id}`, {
        start_date: editingEvent.start_date,
        end_date: editingEvent.end_date
      });
      onUpdate();
      onClose();
      alert('Event updated successfully!');
    } catch (error) {
      console.error('Failed to update event:', error);
      alert('Failed to update event');
    } finally {
      setIsLoading(false);
    }
  };

  const handleDeleteEvent = async () => {
    if (!editingEvent) return;
    
    if (!confirm('Are you sure you want to delete this event?')) {
      return;
    }

    setIsLoading(true);
    try {
      await axios.delete(`http://localhost:8000/api/v1/academic-schedule/events/${editingEvent.id}`);
      onUpdate();
      onClose();
      alert('Event deleted successfully!');
    } catch (error) {
      console.error('Failed to delete event:', error);
      alert('Failed to delete event');
    } finally {
      setIsLoading(false);
    }
  };

  if (!editingEvent) return null;

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-md">
        <DialogHeader>
          <DialogTitle>Edit Event: {editingEvent.event_type}</DialogTitle>
        </DialogHeader>
        
        <div className="space-y-4">
          <div>
            <Label>Start Date</Label>
            <DatePicker
              date={editingEvent.start_date ? parseDate(editingEvent.start_date) : undefined}
              onSelect={(date) => {
                if (date) {
                  setEditingEvent({ ...editingEvent, start_date: formatDateForAPI(date) });
                }
              }}
              placeholder="Pick start date"
            />
          </div>

          <div>
            <Label>End Date (Optional)</Label>
            <DatePicker
              date={editingEvent.end_date ? parseDate(editingEvent.end_date) : undefined}
              onSelect={(date) => {
                if (date) {
                  setEditingEvent({ ...editingEvent, end_date: formatDateForAPI(date) });
                } else {
                  setEditingEvent({ ...editingEvent, end_date: '' });
                }
              }}
              placeholder="Pick end date"
            />
          </div>

          <div className="flex justify-between pt-4">
            <Button
              variant="destructive"
              onClick={handleDeleteEvent}
              disabled={isLoading}
            >
              Delete Event
            </Button>
            <div className="flex gap-2">
              <Button variant="outline" onClick={onClose}>
                <X className="w-4 h-4 mr-1" />
                Cancel
              </Button>
              <Button onClick={handleUpdateEvent} disabled={isLoading}>
                <Save className="w-4 h-4 mr-1" />
                Save Changes
              </Button>
            </div>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}