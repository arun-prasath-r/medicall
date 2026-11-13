import React from 'react';
import { Sun, Sunset, Moon, Clock, Check, AlertCircle } from 'lucide-react';
import {
  format12HourTime,
  calculateDurationMinutes,
  groupSlotsByPeriod,
  formatReadableDate
} from '../../utils/dateTime';

export const TimeSlotPicker = ({
  slots = [],
  selectedSlot = null,
  onSelectSlot,
  selectedDate,
  defaultDuration = 30,
}) => {
  if (!selectedDate) {
    return (
      <div className="time-slots-placeholder">
        <Clock size={32} className="placeholder-icon" />
        <h4>Select a Date to View Open Consultation Times</h4>
        <p>Choose an available date on the calendar to see morning, afternoon, and evening slots.</p>
      </div>
    );
  }

  if (slots.length === 0) {
    return (
      <div className="time-slots-empty">
        <AlertCircle size={28} className="empty-icon" />
        <h4>No Slots Available on {formatReadableDate(selectedDate)}</h4>
        <p>All appointment windows on this date are fully reserved or unavailable. Please choose another date on the calendar.</p>
      </div>
    );
  }

  const { morning, afternoon, evening } = groupSlotsByPeriod(slots);
  const totalAvailable = slots.filter((s) => s.status === 'AVAILABLE').length;

  const renderSection = (title, icon, sectionSlots, timeRangeLabel) => {
    return (
      <div className="time-period-section">
        <div className="time-period-header">
          <div className="time-period-title">
            {icon}
            <span>{title}</span>
            <span className="time-period-range">({timeRangeLabel})</span>
          </div>
          <span className="time-period-count">
            {sectionSlots.filter((s) => s.status === 'AVAILABLE').length} available
          </span>
        </div>

        {sectionSlots.length === 0 ? (
          <div className="time-period-no-slots">
            No {title.toLowerCase()} slots published for this date
          </div>
        ) : (
          <div className="time-slots-grid">
            {sectionSlots.map((slot) => {
              const isSelected = selectedSlot && selectedSlot.id === slot.id;
              const isAvailable = slot.status === 'AVAILABLE';
              const formattedTime = format12HourTime(slot.start_time);
              const duration = calculateDurationMinutes(slot.start_time, slot.end_time) || defaultDuration;

              let pillClass = 'time-slot-pill';
              if (isSelected) pillClass += ' is-selected';
              else if (isAvailable) pillClass += ' is-available';
              else pillClass += ' is-booked';

              return (
                <button
                  type="button"
                  key={slot.id}
                  disabled={!isAvailable}
                  onClick={() => onSelectSlot(slot)}
                  className={pillClass}
                  aria-pressed={isSelected}
                  title={
                    isAvailable
                      ? `${formattedTime} (${duration} mins) - Click to select`
                      : `${formattedTime} - Currently reserved`
                  }
                >
                  <div className="slot-pill-time">
                    <Clock size={13} className="slot-pill-icon" />
                    <span>{formattedTime}</span>
                  </div>
                  <div className="slot-pill-meta">
                    <span className="slot-duration">{duration} min</span>
                    {isSelected && (
                      <span className="slot-check-icon">
                        <Check size={12} strokeWidth={3} />
                      </span>
                    )}
                    {!isAvailable && <span className="slot-status-booked">Booked</span>}
                  </div>
                </button>
              );
            })}
          </div>
        )}
      </div>
    );
  };

  return (
    <div className="time-slot-picker-container">
      <div className="time-picker-summary-bar">
        <div>
          <span className="summary-date-label">Schedule for:</span>
          <strong className="summary-date-value">{formatReadableDate(selectedDate)}</strong>
        </div>
        <span className="badge badge-success">
          {totalAvailable} slot{totalAvailable !== 1 ? 's' : ''} available
        </span>
      </div>

      <div className="time-periods-list">
        {renderSection(
          'Morning',
          <Sun size={17} className="period-icon morning" />,
          morning,
          '06:00 AM – 11:59 AM'
        )}

        {renderSection(
          'Afternoon',
          <Sunset size={17} className="period-icon afternoon" />,
          afternoon,
          '12:00 PM – 04:59 PM'
        )}

        {renderSection(
          'Evening',
          <Moon size={17} className="period-icon evening" />,
          evening,
          '05:00 PM – 11:59 PM'
        )}
      </div>
    </div>
  );
};

