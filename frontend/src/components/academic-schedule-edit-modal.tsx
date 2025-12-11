"use client";

import { useState, useEffect } from 'react';
import { Plus, Edit, Trash2, Save, X } from 'lucide-react';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Label } from '@/components/ui/label';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
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

interface AcademicYear {
  education_year: string;
  year_start: string | null;
  year_end: string | null;
  events: Event[];
}

interface AcademicScheduleEditModalProps {
  year: AcademicYear;
  onUpdate: () => void;
}

export function AcademicScheduleEditModal({ year, onUpdate }: AcademicScheduleEditModalProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [events, setEvents] = useState<Event[]>(year.events);
  const [editingEvent, setEditingEvent] = useState<Event | null>(null);
  const [newEvent, setNewEvent] = useState({
    academic_schedule_id: '',
    type_id: '110000245', // Default type ID
    start_date: '',
    end_date: ''
  });
  const [isLoading, setIsLoading] = useState(false);
  const [showAddForm, setShowAddForm] = useState(false);

  useEffect(() => {
    if (isOpen) {
      setEvents(year.events);
      // Get academic_schedule_id from first event if available
      if (year.events.length > 0) {
        setNewEvent(prev => ({
          ...prev,
          academic_schedule_id: year.events[0].academic_schedule_id
        }));
      }
    }
  }, [isOpen, year.events]);

  const handleCreateEvent = async () => {
    if (!newEvent.academic_schedule_id || !newEvent.start_date) {
      alert('Please fill in required fields (start date is required)');
      return;
    }

    setIsLoading(true);
    try {
      await axios.post('http://localhost:8000/api/v1/academic-schedule/events', newEvent);
      setNewEvent({ 
        academic_schedule_id: newEvent.academic_schedule_id, 
        type_id: '110000245', 
        start_date: '', 
        end_date: '' 
      });
      setShowAddForm(false);
      onUpdate();
      alert('Event created successfully!');
    } catch (error) {
      console.error('Failed to create event:', error);
      alert('Failed to create event');
    } finally {
      setIsLoading(false);
    }
  };

  const handleUpdateEvent = async (eventId: string, updates: { start_date?: string; end_date?: string }) => {
    setIsLoading(true);
    try {
      await axios.put(`http://localhost:8000/api/v1/academic-schedule/events/${eventId}`, updates);
      setEditingEvent(null);
      onUpdate();
      alert('Event updated successfully!');
    } catch (error) {
      console.error('Failed to update event:', error);
      alert('Failed to update event');
    } finally {
      setIsLoading(false);
    }
  };

  const handleDeleteEvent = async (eventId: string) => {
    if (!confirm('Are you sure you want to delete this event?')) {
      return;
    }

    setIsLoading(true);
    try {
      await axios.delete(`http://localhost:8000/api/v1/academic-schedule/events/${eventId}`);
      onUpdate();
      alert('Event deleted successfully!');
    } catch (error) {
      console.error('Failed to delete event:', error);
      alert('Failed to delete event');
    } finally {
      setIsLoading(false);
    }
  };

  const getSemesterColor = (semester: string) => {
    switch (semester) {
      case 'Fall Semester': return 'bg-orange-100 text-orange-800';
      case 'Spring Semester': return 'bg-green-100 text-green-800';
      case 'Summer Semester': return 'bg-blue-100 text-blue-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const formatDateForAPI = (date: Date) => {
    const day = date.getDate().toString().padStart(2, '0');
    const month = (date.getMonth() + 1).toString().padStart(2, '0');
    const year = date.getFullYear();
    return `${day}/${month}/${year}`;
  };

  const parseDate = (dateStr: string) => {
    if (!dateStr) return undefined;
    const [day, month, year] = dateStr.split('/');
    return new Date(parseInt(year), parseInt(month) - 1, parseInt(day));
  };

  return (
    <Dialog open={isOpen} onOpenChange={setIsOpen}>
      <DialogTrigger asChild>
        <Button variant="outline" size="sm" className="ml-2">
          <Edit className="w-4 h-4 mr-1" />
          Edit Events
        </Button>
      </DialogTrigger>
      <DialogContent className="max-w-4xl max-h-[80vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Edit Academic Year Schedule - {year.education_year}</DialogTitle>
        </DialogHeader>
        
        <div className="space-y-4">
          {/* Add New Event Section */}
          <div className="border-b pb-4">
            <div className="flex items-center justify-between mb-2">
              <h3 className="text-lg font-semibold">Events</h3>
              <Button
                onClick={() => setShowAddForm(!showAddForm)}
                variant="outline"
                size="sm"
              >
                <Plus className="w-4 h-4 mr-1" />
                Add Event
              </Button>
            </div>

            {showAddForm && (
              <Card className="mb-4">
                <CardContent className="pt-4">
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div>
                      <Label>Start Date</Label>
                      <DatePicker
                        date={newEvent.start_date ? parseDate(newEvent.start_date) : undefined}
                        onSelect={(date) => {
                          if (date) {
                            setNewEvent({ ...newEvent, start_date: formatDateForAPI(date) });
                          }
                        }}
                        placeholder="Pick start date"
                      />
                    </div>
                    <div>
                      <Label>End Date (Optional)</Label>
                      <DatePicker
                        date={newEvent.end_date ? parseDate(newEvent.end_date) : undefined}
                        onSelect={(date) => {
                          if (date) {
                            setNewEvent({ ...newEvent, end_date: formatDateForAPI(date) });
                          } else {
                            setNewEvent({ ...newEvent, end_date: '' });
                          }
                        }}
                        placeholder="Pick end date"
                      />
                    </div>
                    <div className="flex items-end gap-2">
                      <Button onClick={handleCreateEvent} disabled={isLoading}>
                        <Save className="w-4 h-4 mr-1" />
                        Add Event
                      </Button>
                      <Button variant="outline" onClick={() => setShowAddForm(false)}>
                        <X className="w-4 h-4" />
                      </Button>
                    </div>
                  </div>
                </CardContent>
              </Card>
            )}
          </div>

          {/* Events List */}
          <div className="space-y-2">
            {events.map((event) => (
              <Card key={event.id} className="relative">
                <CardContent className="pt-4">
                  <div className="flex items-center justify-between">
                    <div className="flex-1">
                      {editingEvent?.id === event.id ? (
                        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
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
                          <div className="flex items-end gap-2">
                            <Button
                              size="sm"
                              onClick={() => handleUpdateEvent(event.id, {
                                start_date: editingEvent.start_date,
                                end_date: editingEvent.end_date
                              })}
                              disabled={isLoading}
                            >
                              <Save className="w-4 h-4" />
                            </Button>
                            <Button
                              size="sm"
                              variant="outline"
                              onClick={() => setEditingEvent(null)}
                            >
                              <X className="w-4 h-4" />
                            </Button>
                          </div>
                        </div>
                      ) : (
                        <div className="flex items-center justify-between">
                          <div>
                            <div className="flex items-center gap-2 mb-1">
                              <span className="font-medium">{event.event_type}</span>
                              <Badge className={getSemesterColor(event.semester_type)}>
                                {event.semester_type}
                              </Badge>
                            </div>
                            <div className="text-sm text-gray-600">
                              Start: {event.start_date}
                              {event.end_date && ` | End: ${event.end_date}`}
                            </div>
                          </div>
                          <div className="flex gap-2">
                            <Button
                              size="sm"
                              variant="outline"
                              onClick={() => setEditingEvent(event)}
                            >
                              <Edit className="w-4 h-4" />
                            </Button>
                            <Button
                              size="sm"
                              variant="destructive"
                              onClick={() => handleDeleteEvent(event.id)}
                              disabled={isLoading}
                            >
                              <Trash2 className="w-4 h-4" />
                            </Button>
                          </div>
                        </div>
                      )}
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>

          {events.length === 0 && (
            <div className="text-center py-8 text-gray-500">
              No events found for this academic year.
            </div>
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
}