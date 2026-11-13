import React, { useState } from 'react';
import { ChevronLeft, ChevronRight, Calendar as CalendarIcon, Check } from 'lucide-react';
import { toLocalDateString, formatReadableDate, isPastDate } from '../../utils/dateTime';

const WEEKDAYS = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];

export const AppointmentCalendar = ({
  selectedDate,
  onSelectDate,
  availableDatesMap = {}, // { "2026-11-16": 4, ... }
  minDate = toLocalDateString(new Date()),
  maxDate = null,
}) => {
  // Current viewing month & year in calendar navigation
  const initialDate = selectedDate ? new Date(selectedDate) : new Date();
  const [currentMonth, setCurrentMonth] = useState(initialDate.getMonth());
  const [currentYear, setCurrentYear] = useState(initialDate.getFullYear());

  const todayStr = toLocalDateString(new Date());

  const handlePrevMonth = () => {
    if (currentMonth === 0) {
      setCurrentMonth(11);
      setCurrentYear(currentYear - 1);
    } else {
      setCurrentMonth(currentMonth - 1);
    }
  };

  const handleNextMonth = () => {
    if (currentMonth === 11) {
      setCurrentMonth(0);
      setCurrentYear(currentYear + 1);
    } else {
      setCurrentMonth(currentMonth + 1);
    }
  };

  // Month metadata
  const monthName = new Date(currentYear, currentMonth, 1).toLocaleDateString('en-US', {
    month: 'long',
    year: 'numeric',
  });

  // Calculate calendar grid days
  const firstDayOfWeek = new Date(currentYear, currentMonth, 1).getDay();
  const daysInMonth = new Date(currentYear, currentMonth + 1, 0).getDate();

  // Prev month padding days
  const prevMonthDays = new Date(currentYear, currentMonth, 0).getDate();
  const leadingDays = [];
  for (let i = firstDayOfWeek - 1; i >= 0; i--) {
    leadingDays.push({
      day: prevMonthDays - i,
      isCurrentMonth: false,
    });
  }

  // Days in current month
  const monthDays = [];
  for (let d = 1; d <= daysInMonth; d++) {
    const dateObj = new Date(currentYear, currentMonth, d);
    const dateStr = toLocalDateString(dateObj);
    const isPast = isPastDate(dateStr);
    const isToday = dateStr === todayStr;
    const isSelected = selectedDate === dateStr;
    const slotCount = availableDatesMap[dateStr] || 0;
    const hasSlots = slotCount > 0;
    const isOutOfRange = (minDate && dateStr < minDate) || (maxDate && dateStr > maxDate);
    const isDisabled = isPast || isOutOfRange || !hasSlots;

    monthDays.push({
      day: d,
      dateStr,
      isCurrentMonth: true,
      isToday,
      isSelected,
      hasSlots,
      slotCount,
      isDisabled,
    });
  }

  // Next month padding days to fill 5 or 6 rows (multiples of 7)
  const totalDays = leadingDays.length + monthDays.length;
  const trailingDaysCount = (7 - (totalDays % 7)) % 7;
  const trailingDays = [];
  for (let i = 1; i <= trailingDaysCount; i++) {
    trailingDays.push({
      day: i,
      isCurrentMonth: false,
    });
  }

  // Check if navigating back is allowed (can't navigate earlier than current month of today)
  const isCurrentMonthPast =
    currentYear < new Date().getFullYear() ||
    (currentYear === new Date().getFullYear() && currentMonth <= new Date().getMonth());

  return (
    <div className="appointment-calendar-container">
      {/* Calendar Header with Navigation */}
      <div className="calendar-header">
        <div className="calendar-month-title">
          <CalendarIcon size={18} className="calendar-title-icon" />
          <span>{monthName}</span>
        </div>
        <div className="calendar-nav-buttons">
          <button
            type="button"
            onClick={handlePrevMonth}
            disabled={isCurrentMonthPast}
            className="calendar-nav-btn"
            title="Previous Month"
            aria-label="Previous Month"
          >
            <ChevronLeft size={18} />
          </button>
          <button
            type="button"
            onClick={handleNextMonth}
            className="calendar-nav-btn"
            title="Next Month"
            aria-label="Next Month"
          >
            <ChevronRight size={18} />
          </button>
        </div>
      </div>

      {/* Weekday Labels (Sun - Sat) */}
      <div className="calendar-weekdays-grid">
        {WEEKDAYS.map((wd) => (
          <div key={wd} className="calendar-weekday-cell">
            {wd}
          </div>
        ))}
      </div>

      {/* Calendar Days Grid */}
      <div className="calendar-days-grid">
        {/* Leading padding */}
        {leadingDays.map((item, idx) => (
          <div key={`lead-${idx}`} className="calendar-day-cell is-padding">
            <span className="calendar-day-number">{item.day}</span>
          </div>
        ))}

        {/* Current month days */}
        {monthDays.map((item) => {
          let cellClass = 'calendar-day-cell';
          if (item.isSelected) cellClass += ' is-selected';
          else if (item.hasSlots) cellClass += ' is-available';
          else if (item.isDisabled) cellClass += ' is-disabled';
          if (item.isToday) cellClass += ' is-today';

          return (
            <button
              type="button"
              key={item.dateStr}
              disabled={item.isDisabled}
              onClick={() => onSelectDate(item.dateStr)}
              className={cellClass}
              title={
                item.hasSlots
                  ? `${formatReadableDate(item.dateStr)} (${item.slotCount} slot${item.slotCount > 1 ? 's' : ''} available)`
                  : item.isDisabled
                  ? `${formatReadableDate(item.dateStr)} (No open slots)`
                  : formatReadableDate(item.dateStr)
              }
            >
              <span className="calendar-day-number">{item.day}</span>
              {item.hasSlots && !item.isSelected && (
                <span className="calendar-slot-indicator" />
              )}
              {item.isSelected && (
                <span className="calendar-selected-check">
                  <Check size={10} strokeWidth={3} />
                </span>
              )}
            </button>
          );
        })}

        {/* Trailing padding */}
        {trailingDays.map((item, idx) => (
          <div key={`trail-${idx}`} className="calendar-day-cell is-padding">
            <span className="calendar-day-number">{item.day}</span>
          </div>
        ))}
      </div>

      {/* Legend & Selected Date summary */}
      <div className="calendar-footer-legend">
        <div className="calendar-legend-items">
          <div className="legend-item">
            <span className="legend-dot available" />
            <span>Available</span>
          </div>
          <div className="legend-item">
            <span className="legend-dot selected" />
            <span>Selected</span>
          </div>
          <div className="legend-item">
            <span className="legend-dot unavailable" />
            <span>Unavailable / Full</span>
          </div>
        </div>

        {selectedDate && (
          <div className="calendar-selected-preview">
            <span className="preview-label">Selected Date:</span>
            <strong className="preview-value">{formatReadableDate(selectedDate)}</strong>
          </div>
        )}
      </div>
    </div>
  );
};

